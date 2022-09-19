import asyncio
import inspect
from typing import Coroutine


class TaskCreator:
    loop: asyncio.AbstractEventLoop

    def __init__(self, loop: asyncio.AbstractEventLoop):
        self.loop = loop

    def _caller_name(self) -> str:
        stack = inspect.stack()
        the_module = stack[2][0].f_locals["self"].__module__
        the_class = stack[2][0].f_locals["self"].__class__.__name__
        the_method = stack[2][0].f_code.co_name
        name = f"{the_module}.{the_class}.{the_method}"
        return name

    def create_task_named(self, coro: Coroutine) -> asyncio.Task:
        return self.loop.create_task(coro=coro, name=self._caller_name())

    # async def wait_for(self, fut: Union[Coroutine, asyncio.Future], timeout: Optional[int] = None) -> None:
    #     stack = inspect.stack()
    #     return await asyncio.wait_for(fut=fut, timeout=timeout)
