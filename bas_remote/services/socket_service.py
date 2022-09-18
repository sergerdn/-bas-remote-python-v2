import asyncio
import logging
from typing import Optional

import websockets.legacy.client
from websockets.exceptions import ConnectionClosedError, ConnectionClosedOK
from websockets.legacy.client import WebSocketClientProtocol
from websockets.legacy.client import connect
from websockets.typing import LoggerLike

from bas_remote.errors import SocketNotConnectedError
from bas_remote.types import Message

SEPARATOR = "---Message--End---"


class SocketClosedException(Exception):
    pass


class SocketService:
    """Service that provides methods for interacting with BAS socket."""

    _socket: WebSocketClientProtocol = None

    _buffer: str = ""
    logger: LoggerLike

    def __init__(self, client, logger: Optional[LoggerLike] = None):
        """Create an instance of SocketService class."""
        self._emit = client.emit
        self._loop = client.loop
        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger("[bas-remote:socket]")

    def _connect_websocket(self, port: int, *args, **kwargs) -> websockets.legacy.client.Connect:
        return connect(
            f"ws://127.0.0.1:{port}",
            open_timeout=None,
            max_size=None,
        )

    async def start(self, port: int) -> None:
        """Asynchronously start the socket service with the specified port.

        Arguments:
            port (int): Selected port number.
        """

        attempt = 1
        while not self.is_connected:
            self.logger.debug(f"starting at port: {port}, attempt: {attempt} ...")
            try:
                # TODO: should be configurable
                self._socket = await self._connect_websocket(port=port)
            except ConnectionRefusedError:
                if attempt == 60:
                    raise SocketNotConnectedError()
                await asyncio.sleep(1)
                attempt += 1
        self._opened()

    @property
    def is_connected(self) -> bool:
        return self._socket is not None and self._socket.open

    def _process_data(self, data: str) -> None:
        buffer = (self._buffer + data).split(SEPARATOR)
        for message in [item for item in buffer if item]:
            unpacked = Message.from_json(message)  # type: ignore
            self._emit("message_received", unpacked)
        self._buffer = buffer.pop()

    def _closed(self) -> None:
        """Function that is called when the connection is closed."""
        self._emit("socket_close")
        self._loop.create_task(self.close())

    def _opened(self) -> None:
        """Function that is called when the connection is opened."""
        self._emit("socket_open")
        self._loop.create_task(self.listen())

    async def listen(self) -> None:
        while True:
            try:
                data = await self._socket.recv()
                self._process_data(data)
            except ConnectionClosedError:
                break
            except ConnectionClosedOK:
                break
        self.logger.info("connection closed")
        self._closed()

    async def send(self, message: Message) -> int:
        packet = message.to_json() + SEPARATOR  # type: ignore
        await self._socket.send(packet)
        self._emit("message_sent", message)
        return message.id_

    async def close(self, silence=False) -> None:
        """Close the socket service."""
        exc = SocketClosedException("connections accidentally closed: %s", self._socket.close_sent)

        if not self.is_connected:
            if not silence:
                raise exc
            return

        if self._socket.closed:
            self.logger.info("connections closed: %s", self._socket.close_sent)
            if not silence:
                raise exc
            return

        await self._socket.close()
        if not silence:
            raise exc


__all__ = ["SocketService"]
