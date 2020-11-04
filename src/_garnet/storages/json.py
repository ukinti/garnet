import json
import pathlib
import typing

from _garnet.concurrency import to_thread

from .dict import DictStorage, _UserStorageMetaData
from .typedef import StorageDataT


def _create_json_file(path: pathlib.Path) -> None:
    if not path.exists():
        with path.open("w", encoding="utf-8") as f:
            f.write("{}")

    return None


class JSONStorage(DictStorage[StorageDataT]):
    """
    JSON File storage based on DictStorage
    """

    def __init__(self, path: typing.Union[pathlib.Path, str]):
        super().__init__()
        self._path = pathlib.Path(path)

    async def init(self) -> None:
        def _read() -> _UserStorageMetaData:
            _create_json_file(self._path)
            with self._path.open("r", encoding="utf-8") as fp:
                return json.load(fp)

        data = await to_thread(_read)
        self._data = data

        return await super().init()

    async def close(self) -> None:
        def _save() -> None:
            with self._path.open("w", encoding="utf-8") as fp:
                json.dump(self._data, fp, ensure_ascii=False)
            return None

        await to_thread(_save)

        return await super().close()
