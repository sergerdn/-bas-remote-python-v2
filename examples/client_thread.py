import asyncio

import yaml

from bas_remote import BasRemoteClient, Options
from examples.settings import remote_script_name, remote_script_password, remote_script_user, working_dir


async def main():
    client = BasRemoteClient(
        options=Options(
            script_name=remote_script_name,
            login=remote_script_user,
            password=remote_script_password,
            working_dir=working_dir,
        ),
    )

    await client.start()
    client_thread = client.create_thread()

    data = await client_thread.run_function("TestReturnBigData")
    data_obj = yaml.load(data, Loader=yaml.UnsafeLoader)
    print(data_obj[0])

    await client_thread.stop()
    await client.close()


if __name__ == "__main__":
    asyncio.run(main())
