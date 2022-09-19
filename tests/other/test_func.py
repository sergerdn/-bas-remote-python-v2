import asyncio
import time

import psutil
import pytest
import websockets
import yaml
from pytest_mock import MockerFixture
from websockets.legacy.client import connect

import bas_remote
from bas_remote import BasRemoteClient, Options
from bas_remote.runners import BasThread


@pytest.mark.asyncio
class TestFuncMultiple:
    async def test_check_ip(self, client_thread: BasThread):
        result = await client_thread.run_function("CheckIp")
        print(result)

    async def test_check_ip_json(self, client_thread: BasThread):
        result = await client_thread.run_function("CheckIpJson")
        print(result)

    async def test_return_big_data(self, client_thread: BasThread):
        data = await client_thread.run_function("TestReturnBigData")
        data_obj = yaml.load(data, Loader=yaml.UnsafeLoader)
        assert len(data_obj) > 1
        for one in data_obj:
            assert sorted(
                [
                    "body",
                    "error",
                    "is_error",
                    "is_finished",
                    "post_data",
                    "request_headers",
                    "response_headers",
                    "status",
                    "url",
                ]
            ) == sorted(one.keys())

    @pytest.mark.timeout(timeout=60 * 3)
    async def test_task_websocket_closed(
        self, client_options: Options, event_loop: asyncio.AbstractEventLoop, mocker: MockerFixture
    ):
        class SocketServicePatched:
            def _connect_websocket(self, port: int, *args, **kwargs) -> websockets.legacy.client.Connect:
                return connect(
                    f"ws://127.0.0.1:{port}",
                    open_timeout=None,
                )

        from bas_remote.services import SocketService

        mocker.patch.object(
            target=bas_remote.services.SocketService,
            attribute="_connect_websocket",
            new=SocketServicePatched._connect_websocket,
        )
        client = BasRemoteClient(
            options=client_options,
            loop=event_loop,
        )

        await client.start()
        thread = client.create_thread()

        """because connection closed"""
        with pytest.raises(asyncio.exceptions.CancelledError):
            await thread.run_function("TestReturnBigData")

        await client.close()

    @pytest.mark.timeout(timeout=60 * 3)
    async def test_process_killed(self, client_options: Options, event_loop: asyncio.AbstractEventLoop):
        # poetry run pytest tests/other/ -k "test_process_killed"
        client = BasRemoteClient(
            options=client_options,
            loop=event_loop,
        )

        await client.start()
        thread = client.create_thread()

        proc_found = False
        for proc in psutil.process_iter():
            if proc.name() == "FastExecuteScript.exe":
                if client.options.working_dir in proc.cmdline()[0]:
                    proc_found = True
                    proc.terminate()
                    with pytest.raises(psutil.NoSuchProcess):
                        for _ in range(0, 60):
                            time.sleep(1)
                            psutil.Process(pid=proc.pid)
            if proc_found:
                break
        assert proc_found is True

        """because process killed and connection closed"""
        with pytest.raises(asyncio.exceptions.CancelledError):
            await thread.run_function("CheckIpJson")
