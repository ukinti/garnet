# Source: https://github.com/aiogram/aiogram
# MODIFIED.
import functools
import json
import pathlib
import typing

from _garnet.concurrency import to_thread

from .memory import MemoryStorage


def _create_json_file(path: pathlib.Path):
    """
    Write initials to JSON file
    """
    if not path.exists():
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
        super().__init__()
        self.path = pathlib.Path(path)

    def _read(self):
        _create_json_file(self.path)
        with self.path.open("r", encoding="utf-8") as fp:
            return json.load(fp,)

    def _save(self):
        with self.path.open("w", encoding="utf-8") as fp:
            return json.dump(self.data, fp, ensure_ascii=False)

    async def init(self) -> None:
        data = await to_thread(functools.partial(self._read, self.path))
        self.data = data

    async def save(self) -> None:
        if self.data:
            await to_thread(functools.partial(self.save, self.path))
        await super().close()
