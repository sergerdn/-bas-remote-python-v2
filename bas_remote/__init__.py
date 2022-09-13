from .client import BasRemoteClient
from .errors import *
from .options import Options
from .types import Message

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
__version__ = "2.0.0"
__license__ = "MIT"
