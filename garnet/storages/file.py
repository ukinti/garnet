# Source: https://github.com/aiogram/aiogram
# MODIFIED.

import asyncio
import pathlib
import typing
from concurrent.futures import ThreadPoolExecutor

from ..jsonlib import json
from .memory import MemoryStorage

executor = ThreadPoolExecutor()
loop = asyncio.get_event_loop()


def _create_json_file(path: pathlib.Path):
    """
    Since `orJSON` does not provide .dump write by hand.
    """
    with path.open("w", encoding="utf-8") as f:
        f.write("{}")


class JSONStorage(MemoryStorage):
    """
    JSON File storage based on MemoryStorage
    """

    def __init__(self, path: typing.Union[pathlib.Path, str]):
        """
        Creates if not found, saves if process was closed properly.
        Could be more reliable.
        :param path: file path
        """
        self.path = path = pathlib.Path(path)
        try:
            data = self.__read(path)
        except FileNotFoundError:
            _create_json_file(path)
            data = self.__read(path)

        super().__init__(data)

    # noinspection PyMethodMayBeStatic
    def __read(self, path: pathlib.Path):
        with path.open("r", encoding="utf-8") as f:
            return json.loads(f.read())

    def _save(self, path: pathlib.Path):
        with path.open("w", encoding="utf-8") as f:
            return f.write(json.dumps(self.data).decode())

    async def save(self, close: bool = False):
        if self.data:
            await loop.run_in_executor(executor, self.save, self.path)
        if close:
            await super().close()
