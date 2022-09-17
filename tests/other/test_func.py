import pytest
import yaml

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

    @pytest.mark.timeout(60)
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
