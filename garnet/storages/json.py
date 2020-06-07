# Source: https://github.com/aiogram/aiogram
# MODIFIED.

import asyncio
import pathlib
import typing
from concurrent.futures import ThreadPoolExecutor

from ..jsonlib import json
from .memory import MemoryStorage
from .base import FileStorageProto

executor = ThreadPoolExecutor()
loop = asyncio.get_event_loop()


def _create_json_file(path: pathlib.Path):
    """
    Since `orJSON` does not provide .dump write by hand.
    """
    if not path.exists():
        with path.open("w", encoding="utf-8") as f:
            f.write("{}")


class JSONStorage(MemoryStorage, FileStorageProto):
    """
    JSON File storage based on MemoryStorage
    """

    def __init__(self, path: typing.Union[pathlib.Path, str]):
        """
        Creates if not found, saves if process was closed properly.
        Could be more reliable.
        :param path: file path
        """
        super().__init__()
        self.path = pathlib.Path(path)

    # noinspection PyMethodMayBeStatic
    def __read(self, path: pathlib.Path):
        _create_json_file(path)
        with path.open("r", encoding="utf-8") as f:
            return json.loads(f.read())

    def _save(self, path: pathlib.Path):
        with path.open("wb", encoding="utf-8") as f:
            serialized = json.dumps(self.data)  # orjson returns bytes for dumps
            return f.write(serialized if isinstance(serialized, bytes) else serialized.encode())

    async def read(self) -> None:
        data = await loop.run_in_executor(executor, self.__read, self.path)
        self.data = data

    async def save(self, close: bool = False) -> None:
        if self.data:
            await loop.run_in_executor(executor, self.save, self.path)
        if close:
            await super().close()
