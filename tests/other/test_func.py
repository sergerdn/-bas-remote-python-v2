import pytest

from bas_remote.runners import BasThread


@pytest.mark.asyncio
class TestFuncMultiple:
    @pytest.mark.timeout(60)
    async def test_function_check_ip(self, client_thread: BasThread):
        result = await client_thread.run_function("CheckIp")
        print(result)

    @pytest.mark.timeout(60)
    async def test_function_check_ip_json(self, client_thread: BasThread):
        result = await client_thread.run_function("CheckIpJson")
        print(result)

    @pytest.mark.skip(reason="no way to fix it at the moment")
    @pytest.mark.timeout(60)
    async def test_function_return_big_data(self, client_thread: BasThread):
        result = await client_thread.run_function("TestReturnBigData")
        print(result)
