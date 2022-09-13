import asyncio
import os.path
import unittest

from bas_remote import BasRemoteClient, Options
from tests import ABS_PATH, test_remote_script_password
from tests import test_remote_script_name, test_remote_script_user


class BaseTest(unittest.TestCase):
    client = None

    loop = None

    @classmethod
    def setUpClass(cls) -> None:
        cls.loop = asyncio.new_event_loop()

        script_name = test_remote_script_name
        remote_script_user = test_remote_script_user
        remote_script_password = test_remote_script_password

        working_dir = os.path.join(ABS_PATH, ".bas-remote-app-{script_name}".format(script_name=script_name.lower()))
        if not os.path.exists:
            os.mkdir(working_dir)

        cls.options = Options(
            working_dir=working_dir, script_name=script_name, login=remote_script_user, password=remote_script_password
        )
        cls.client = BasRemoteClient(cls.options, cls.loop)
        cls.loop.run_until_complete(cls.client.start())

    @classmethod
    def tearDownClass(cls) -> None:
        cls.loop.run_until_complete(cls.client.close())
        cls.loop.close()

    def run_functions(self, runner, x: list, y: list):
        tasks = []
        for i in range(len(x)):
            executor = runner if isinstance(runner, BasRemoteClient) else runner[i]
            tasks.append(self.loop.create_task(get_func(executor, x[i], y[i])))
        return self.loop.run_until_complete(asyncio.gather(*tasks))

    def run_function(self, runner, x: int, y: int):
        return self.loop.run_until_complete(get_func(runner, x, y))

    def run_fail(self, runner, x: int, y: int):
        return self.loop.run_until_complete(get_func(runner, x, y, "Add1"))


async def get_func(runner, x: int, y: int, name: str = "Add"):
    return await runner.run_function(name, {"X": x, "Y": y})
