from .client import BasRemoteClient
from bas_remote.errors import BasError, SocketNotConnectedError, ScriptNotSupportedError, ClientNotStartedError
from bas_remote.errors import ScriptNotExistError, AuthenticationError, AlreadyRunningError, FunctionError
from bas_remote.options import Options
from bas_remote.types import Message

__all__ = [
    "BasRemoteClient",
    "SocketNotConnectedError",
    "ScriptNotSupportedError",
    "ClientNotStartedError",
    "ScriptNotExistError",
    "AuthenticationError",
    "AlreadyRunningError",
    "FunctionError",
    "BasError",
    "Options",
    "Message",
]

__author__ = "CheshireCaat"
__version__ = "2.0.1"
__license__ = "MIT"
