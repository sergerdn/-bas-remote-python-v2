import asyncio

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
    async def test_function_check_ip(self, client_thread: BasThread):
        result = await client_thread.run_function("CheckIp")
        print(result)

    async def test_function_check_ip_json(self, client_thread: BasThread):
        result = await client_thread.run_function("CheckIpJson")
        print(result)

    async def test_function_return_big_data(self, client_thread: BasThread):
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

    async def test_function_task_canceled_error(
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

    async def test_function_process_killed(self, client_options: Options, event_loop: asyncio.AbstractEventLoop):
        client = BasRemoteClient(
            options=client_options,
            loop=event_loop,
        )

        await client.start()
        thread = client.create_thread()

        proc = None
        for proc in psutil.process_iter():
            if proc.name() == "FastExecuteScript.exe":
                break

        assert proc is not None

        with pytest.raises(asyncio.exceptions.CancelledError):
            proc.terminate()
            await asyncio.sleep(60)

        with pytest.raises(psutil.NoSuchProcess):
            for _ in range(0, 60):
                psutil.Process(pid=proc.pid)
                await asyncio.sleep(1)

        """because process killed and connection closed"""
        with pytest.raises(asyncio.exceptions.CancelledError):
            await thread.run_function("CheckIpJson")
