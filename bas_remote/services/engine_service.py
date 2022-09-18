import asyncio
import logging
import subprocess
from os import listdir, makedirs, path
from platform import machine
from shutil import rmtree
from typing import Optional
from zipfile import ZipFile

from aiofiles import open
from aiohttp import ClientSession
from filelock import FileLock, Timeout, BaseFileLock
from websockets.typing import LoggerLike

from bas_remote.errors import ScriptNotExistError, ScriptNotSupportedError
from bas_remote.types import Script

END_POINT = "https://bablosoft.com"


class EngineService:
    """Service that provides methods for interacting with BAS engine."""

    _exe_dir: str = None
    """The path to the directory in which the executable file of the engine is located."""

    _zip_dir: str = None
    """The path to the directory in which the archive file of the engine is located."""

    logger: LoggerLike
    _lock: Optional[BaseFileLock] = None

    def __init__(self, client, logger: Optional[LoggerLike] = None):
        """Create an instance of EngineService class."""
        script_name = client.options.script_name
        working_dir = client.options.working_dir
        self._loop = client.loop

        self._script_dir = path.join(working_dir, "run", script_name)
        self._engine_dir = path.join(working_dir, "engine")
        self._script_name = script_name

        self._process = None

        if logger is not None:
            self.logger = logger
        else:
            self.logger = logging.getLogger("[bas-remote:engine]")

    async def start(self, port: int) -> None:
        """Asynchronously start the engine service with the specified port.

        Arguments:
            port (int):
                Selected port number.
        """

        arch = 64 if machine().endswith("64") else 32
        zip_name = f"FastExecuteScriptProtected.x{arch}"
        url_name = f"FastExecuteScriptProtected{arch}"

        zip_path = path.join(self._zip_dir, f"{zip_name}.zip")

        self.logger.debug(f"start at port :{port}, arch:{arch}, zip_name:{zip_name}, url_name:{url_name}")

        if not path.exists(self._zip_dir):
            makedirs(self._zip_dir)
            await self._download_executable(zip_path, zip_name, url_name)

        if not path.exists(self._exe_dir):
            makedirs(self._exe_dir)
            await self._extract_executable(zip_path)

        self._start_engine_process(port)
        self._clear_run_directory()

    async def initialize(self):
        url = f"{END_POINT}/scripts/{self._script_name}/properties"

        async with ClientSession(loop=self._loop) as session:
            async with session.get(url) as response:
                script = Script(await response.json())

        if not script.is_exist:
            raise ScriptNotExistError()

        if not script.is_supported:
            raise ScriptNotSupportedError()

        self._zip_dir = path.join(self._engine_dir, script.engine_version)
        self._exe_dir = path.join(self._script_dir, script.hash[0:5])

    async def _download_executable(self, zip_path: str, zip_name: str, url_name: str) -> None:
        url = f"{END_POINT}/distr/{url_name}/{path.basename(self._zip_dir)}/{zip_name}.zip"
        self.logger.debug(f"download executable: {url}")

        async with ClientSession(loop=self._loop) as session:
            async with session.get(url) as response:
                async with open(zip_path, "wb") as file:
                    while True:
                        chunk = await response.content.read(1024 * 16)
                        if not chunk:
                            break
                        await file.write(chunk)
                    return await response.release()

    async def _extract_executable(self, zip_path: str) -> None:
        self.logger.debug(f"extract executable: {zip_path}")

        with ZipFile(zip_path, "r") as file:
            async def task(name, zip_file: ZipFile):
                zip_file.extract(name, self._exe_dir, None)

            await asyncio.wait([task(name, file) for name in file.namelist()])

    def _start_engine_process(self, port: int) -> None:
        cmd = [path.join(self._exe_dir, "FastExecuteScript.exe"), f"--remote-control-port={port}", "--remote-control"]
        cwd = self._exe_dir

        self.logger.debug(f"start engine process: {cmd}, {cwd}")

        self._process = subprocess.Popen(cmd, cwd=cwd)
        self.lock_acquire()

    def lock_acquire(self):
        lock = self._get_lock_path()
        self._lock = FileLock(lock, timeout=5)
        self.logger.debug(f"lock: {self._lock.lock_file}")
        self._lock.acquire()

    def lock_release(self):
        if self._lock:
            self._lock.release(force=True)

    def _clear_run_directory(self) -> None:
        for dir_path in [name for name in listdir(self._script_dir) if path.isfile(name)]:
            dir_path = path.join(self._script_dir, dir_path)
            lock_path = self._get_lock_path(dir_path)
            if not is_locked(lock_path):
                rmtree(dir_path)

    def _get_lock_path(self, dir_path=None) -> str:
        return path.join(dir_path or self._exe_dir, ".lock")

    async def close(self) -> None:
        """Close the engine service."""
        self.logger.info("closing...")
        self._process.kill()
        self.lock_release()


def is_locked(lock_path):
    try:
        with FileLock(lock_path, timeout=0.5) as lock:
            with lock.acquire():
                return False
    except Timeout:
        return True


__all__ = ["EngineService"]
