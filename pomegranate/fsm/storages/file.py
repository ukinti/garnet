import asyncio
import pathlib
import typing
from concurrent.futures import ThreadPoolExecutor

from ...jsonlib import json
from .memory import MemoryStorage

executor = ThreadPoolExecutor()
loop = asyncio.get_event_loop()


def _create_json_file(path: pathlib.Path):
    with path.open("w") as f:
        f.write("{}")


class JSONStorage(MemoryStorage):
    """
    JSON File storage based on MemoryStorage
    """

    def __init__(self, path: typing.Union[pathlib.Path, str], reload_each: int = 360):
        """
        :param path: file path
        :param reload_each: reload json file every n sec
        """
        self.path = pathlib.Path(path)
        try:
            data = self.__read(path)
        except FileNotFoundError:
            _create_json_file(path)
            data = self.__read(path)

        super().__init__(data)

        if reload_each is False:
            loop.create_task(self.__reload(reload_each))

    @staticmethod
    def __read(path: pathlib.Path):
        with path.open('r') as f:
            return json.load(f)

    def __write(self, path: pathlib.Path):
        with path.open('w') as f:
            return json.dump(self.data, f, indent=4)

    async def __reload(self, delay: int):
        while 1:
            await asyncio.sleep(delay)
            await loop.run_in_executor(executor, self.__write, self.path)

    async def close(self):
        if self.data:
            await loop.run_in_executor(executor, self.__write, self.path)
        await super().close()
