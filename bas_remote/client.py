import asyncio
import json
import logging
import socket
from asyncio import Future
from contextlib import closing
from random import randint
from typing import Callable, Optional, Dict, Any

from pyee.asyncio import AsyncIOEventEmitter
from websockets.typing import LoggerLike

from bas_remote.errors import AuthenticationError, ClientNotStartedError
from bas_remote.options import Options
from bas_remote.runners import BasFunction, BasThread
from bas_remote.services import EngineService, SocketService
from bas_remote.task import TaskCreator
from bas_remote.types import Message


class BasRemoteClient(AsyncIOEventEmitter):
    """Class that provides methods for remotely interacting with BAS."""

    _requests: Dict[int, Callable] = {}
    """Dictionary of requests handlers."""

    _engine: EngineService = None
    """Client engine service object."""

    _socket: SocketService = None
    """Client socket service object"""

    _is_started: bool = False

    _future: Future = None

    logger: LoggerLike
    port: int
    _task_creator: TaskCreator

    def __init__(
        self,
        options: Options,
        loop: Optional[asyncio.AbstractEventLoop] = None,
        logger: Optional[LoggerLike] = None,
    ):
        """Create an instance of BasRemoteClient class.

        Args:
            options (Options): Remote control options object.
            loop (AbstractEventLoop, optional): AsyncIO event loop object. Defaults to None.
        """
        self.loop = loop or asyncio.get_event_loop()
        self.loop.set_exception_handler(handler=self._exception_handler)
        super().__init__(self.loop)
        self.options = options

        self._future = self.loop.create_future()
        self._engine = EngineService(self)
        self._socket = SocketService(self)

        self.on("message_received", self._on_message_received)
        self.on("socket_open", self._on_socket_open)
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger("[bas-remote:client]")

        self._task_creator = TaskCreator(loop=self._loop)

    @property
    def is_started(self):
        """Gets a value that indicates whether the current client is already running."""
        return self._is_started

    def _exception_handler(self, loop, context, *args, **kwargs):
        """should not be reached here in normal situation"""
        self.logger.error(context)
        for task in asyncio.all_tasks(loop=self.loop):
            coro = task.get_coro()
            """cancel only stopped task"""
            if not coro.cr_running:
                self.logger.debug(task)
                task.cancel("fatal error occurred")

    async def start(self) -> None:
        """Start the client and wait for it initialize."""
        await self._engine.initialize()

        def find_free_port():
            with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
                s.bind(("", 0))
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                return s.getsockname()[1]

        self.port = find_free_port()
        self.logger.info("running at port: %s" % self.port)
        await self._engine.start(self.port)
        await self._socket.start(self.port)
        await asyncio.wait_for(fut=self._future, timeout=60)

    async def _on_message_received(self, message: Message) -> None:
        self.logger.debug("message received: %s" % message)

        if message.type_ == "initialize":
            await self._send("accept_resources", {"-bas-empty-script-": True})
        elif message.type_ == "thread_start" and not self._future.done():
            self._future.set_result(True)
            self._is_started = True
        elif message.type_ == "message" and not self._future.done():
            self._future.set_exception(AuthenticationError())
            self._is_started = False
        elif message.async_ and message.id_:
            callback = self._requests.pop(message.id_)
            if message.type_ == "get_global_variable":
                callback(json.loads(message.data))
            else:
                callback(message.data)

    async def _on_socket_open(self) -> None:
        await self._send(
            "remote_control_data",
            {
                "script": self.options.script_name,
                "password": self.options.password,
                "login": self.options.login,
            },
        )

    def run_function(self, function_name: str, function_params: Optional[Dict] = None) -> BasFunction:
        """Call the BAS function asynchronously.

        Args:
            function_name (str): BAS function name as string.
            function_params (dict, optional): BAS function arguments list. Defaults to None.
        """
        if not self.is_started:
            raise ClientNotStartedError()
        return BasFunction(self, function_name, function_params)

    async def send(self, type_: str, data: Optional[Dict] = None, async_: bool = False) -> int:
        """Send the custom message asynchronously and get message id as result.

        Args:
            type_ (str): Selected message type.
            data (dict, optional): Message arguments. Defaults to None.
            async_ (bool): Is message async. Defaults to False.

        Returns:
            int: Message id number.
        """
        if not self.is_started:
            raise ClientNotStartedError()
        return await self._send(type_, data, async_)

    async def send_async(self, type_: str, data: Optional[Dict] = None) -> Any:
        """Send the custom message asynchronously and get result.

        Args:
            type_ (str): Selected message type.
            data (dict, optional): Message arguments. Defaults to None.
        """
        if not self.is_started:
            raise ClientNotStartedError()
        return await self._send_async(type_, data)

    async def _send(self, type_: str, data: Optional[Dict] = None, async_=False) -> int:
        message = Message(
            data={} if not data else data,
            id_=randint(100000, 999999),
            async_=async_,
            type_=type_,
        )
        self.logger.debug("message send: %s" % message)
        return await self._socket.send(message=message)

    async def _send_async(self, type_: str, data: Optional[Dict] = None) -> Any:
        future = self.loop.create_future()
        id_ = await self.send(type_, data, True)
        self._requests[id_] = lambda result: future.set_result(result)

        return await future

    async def start_thread(self, thread_id: int) -> None:
        """Start thread with specified id.

        Args:
            thread_id (int): Thread identifier.
        """
        await self.send("start_thread", {"thread_id": thread_id})

    async def stop_thread(self, thread_id: int) -> None:
        """Stop thread with specified id.

        Args:
            thread_id (int): Thread identifier.
        """
        await self.send("stop_thread", {"thread_id": thread_id})

    def create_thread(self) -> BasThread:
        """Create new BAS thread object.

        Returns:
            BasThread: Thread object.
        """
        return BasThread(self)

    async def close(self) -> None:
        """Close the client."""
        await self._socket.close(expected=True)

        await self._engine.close()
        self._engine.lock_release()
        self._is_started = False


__all__ = ["BasRemoteClient"]
