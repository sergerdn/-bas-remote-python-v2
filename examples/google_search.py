import asyncio

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

    try:
        result = await client.run_function("GoogleSearch", {"Query": "cats"})
        for link in result:
            print(link)
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
