import asyncio

import psutil
import pytest
import websockets
import yaml
from pytest_mock import MockerFixture
from websockets.legacy.client import connect

import bas_remote
from bas_remote import BasRemoteClient, Options
from bas_remote.errors import FunctionFatalError
from bas_remote.runners import BasThread


def kill_process(working_dir: str, event_loop: asyncio.AbstractEventLoop) -> bool:
    proc_found = False
    for proc in psutil.process_iter():
        if proc.name() == "FastExecuteScript.exe":
            if working_dir in proc.cmdline()[0]:
                proc_found = True
                proc.terminate()
                while 1:
                    event_loop.run_until_complete(asyncio.sleep(1))
                    try:
                        psutil.Process(pid=proc.pid)
                    except psutil.NoSuchProcess:
                        break
        if proc_found:
            break
    return proc_found


@pytest.mark.asyncio
class TestFuncMultiple:
    @pytest.mark.skip("skipped")
    async def test_check_ip(self, client_thread: BasThread):
        result = await client_thread.run_function("CheckIp")
        print(result)

    @pytest.mark.skip("skipped")
    async def test_check_ip_json(self, client_thread: BasThread):
        result = await client_thread.run_function("CheckIpJson")
        print(result)

    @pytest.mark.skip("skipped")
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
    async def test_task_websocket_closed_thread(
        self, client_options: Options, event_loop: asyncio.AbstractEventLoop, mocker: MockerFixture
    ):
        # poetry run pytest tests/other/ -k "test_task_websocket_closed_thread"
        class SocketServicePatched:
            def _connect_websocket(self, port: int, *args, **kwargs) -> websockets.legacy.client.Connect:
                return connect(
                    f"ws://127.0.0.1:{port}",
                    open_timeout=10,
                )

        from bas_remote.services import SocketService  # type: ignore

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
        await thread.start()

        """because connection closed"""
        try:
            try:
                await thread.run_function("TestReturnBigData")
            except FunctionFatalError as exc:
                assert True
            else:
                assert False
        finally:
            await client.close()

    @pytest.mark.timeout(timeout=60 * 3)
    async def test_process_killed_thread(self, client_options: Options, event_loop: asyncio.AbstractEventLoop):
        # poetry run pytest tests/other/ -k "test_process_killed_thread"
        client = BasRemoteClient(
            options=client_options,
            loop=event_loop,
        )

        await client.start()
        thread = client.create_thread()
        await thread.start()

        assert kill_process(client.options.working_dir, event_loop) is True

        """because process killed and connection closed"""
        try:
            try:
                await thread.run_function("CheckIpJson")
            except FunctionFatalError as exc:
                assert True
            else:
                assert False
        finally:
            await client.close()
