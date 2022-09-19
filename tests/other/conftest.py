import asyncio
import os

import pytest

from bas_remote import BasRemoteClient, Options
from bas_remote.runners import BasThread
from tests import test_app_working_dir


@pytest.fixture(scope="module")
def remote_script_name(request):
    return os.environ.get("TEST_REMOTE_SCRIPT_NAME", "TestRemoteControlV2")


@pytest.fixture(scope="module")
def remote_script_user(request):
    return os.environ.get("TEST_REMOTE_SCRIPT_USER")


@pytest.fixture(scope="module")
def remote_script_password(request):
    return os.environ.get("TEST_REMOTE_SCRIPT_PASSWORD")


@pytest.fixture(scope="module")
def working_dir():
    return test_app_working_dir


@pytest.fixture(scope="function")
def event_loop() -> asyncio.AbstractEventLoop:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    if loop.is_closed():
        return
    loop.close()


@pytest.fixture(scope="function")
def client_options(
        event_loop: asyncio.AbstractEventLoop,
        working_dir,
        remote_script_name,
        remote_script_user,
        remote_script_password,
) -> Options:
    yield Options(
        script_name=remote_script_name,
        login=remote_script_user,
        password=remote_script_password,
        working_dir=working_dir,
    )


@pytest.fixture(scope="function")
def client_thread(
        event_loop: asyncio.AbstractEventLoop,
        client_options,
) -> BasThread:
    client = BasRemoteClient(
        options=client_options,
        loop=event_loop,
    )

    event_loop.run_until_complete(client.start())
    thread = client.create_thread()

    yield thread

    event_loop.run_until_complete(thread.stop())
    event_loop.run_until_complete(client.close())
