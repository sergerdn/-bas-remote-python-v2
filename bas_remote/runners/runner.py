import json
import logging
from abc import ABC, abstractmethod
from asyncio import Future, AbstractEventLoop
from typing import Optional, Dict

from websockets.typing import LoggerLike

from bas_remote.errors import FunctionError, NetworkFatalError, FunctionFatalError
from bas_remote.types import Response


class BasRunner(ABC):
    _loop: AbstractEventLoop = None

    _future: Future = None

    _id: int = 0
    logger: LoggerLike

    def __init__(self, client, logger: Optional[LoggerLike] = None):
        """Create an instance of Runner class.

        Args:
            client: Remote client object.
        """
        self._loop = client.loop
        self._client = client
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger("[bas-remote:runner]")

    def __await__(self):
        return self._future.__await__()

    def _run(self, name: str, params: Optional[Dict] = None):
        self._future = self._loop.create_future()
        task = self._run_function(name, params)
        self._loop.create_task(task)

    @abstractmethod
    async def _run_function(self, name: str, params: Optional[Dict] = None):
        """Run the BAS function asynchronously.

        Args:
            name (str): BAS function name as string.
            params (dict, optional): BAS function arguments list.
        """
        pass

    async def _run_task(self, name: str, params: Optional[Dict] = None):
        """Run the BAS task asynchronously.

        Args:
            name (str): BAS function name as string.
            params (dict, optional): BAS function arguments list.
        """
        try:
            result = await self._client.send_async(
                "run_task",
                {"params": json.dumps(params if params else {}), "function_name": name, "thread_id": self.id}
            )
        except NetworkFatalError as exc:
            self.logger.error(exc)
            exception = FunctionFatalError(str(exc))
            self._future.set_exception(exception)
            return
        except Exception as exc:
            self.logger.error(exc)
            exception = FunctionFatalError(str(exc))
            self._future.set_exception(exception)
            return

        response = Response.from_json(result)  # type: ignore
        if not response.success:
            exception = FunctionError(response.message)
            self._future.set_exception(exception)
        else:
            self._future.set_result(response.result)

    @property
    def id(self) -> int:
        """Gets current thread id."""
        return self._id


__all__ = ["BasRunner"]
