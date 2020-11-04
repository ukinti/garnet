import abc
from typing import Generic, Optional

from .typedef import StorageDataT


class BaseStorage(Generic[StorageDataT], abc.ABC):
    @abc.abstractmethod
    async def get_state(self, key: str) -> Optional[str]:
        """Read the current state for {key} and return it as string."""
        raise NotImplementedError

    @abc.abstractmethod
    async def set_state(self, key: str, state: Optional[str]) -> None:
        """
        Overwrite existing state to the passed one.

        (!) If None was passed as ``state``, then underlying state should
        become ``None`` too and not any kind of string.
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def get_data(self, key: str) -> Optional[StorageDataT]:
        """
        Read the current data and return it as StorageDataT

        (!) If there is a data, otherwise ``None`` should be returned
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def set_data(self, key: str, data: Optional[StorageDataT]) -> None:
        """
        Overwrite existing data to a new passed one

        (!) If None was passed as ``data``, then data should become ``None``
        too, and not any kind of empty/uninitialized of STORAGE_DATA_T
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def update_data(self, key: str, data: StorageDataT) -> None:
        """
        Merge passed data to an existing one.
        """
        raise NotImplementedError

    # naively implemented basic, base member methods
    async def reset_state(self, key: str) -> None:
        await self.set_state(key=key, state=None)

    async def reset_data(self, key: str) -> None:
        await self.set_data(key=key, data=None)

    async def reset(self, key: str) -> None:
        """Reset both state and data."""
        await self.reset_state(key=key)
        await self.reset_data(key=key)

    @abc.abstractmethod
    async def init(self) -> None:
        """First call for storage during garnet runtime"""
        raise NotImplementedError

    @abc.abstractmethod
    async def close(self) -> None:
        """Latest call for storage during garnet runtime."""
        raise NotImplementedError
