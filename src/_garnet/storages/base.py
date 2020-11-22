import abc
from typing import Callable, Generic, Optional

from .typedef import StorageDataT


class BaseStorage(Generic[StorageDataT], abc.ABC):
    __slots__ = ("_data_data_factory",)

    def __init__(
        self, data_factory: Callable[[], StorageDataT],
    ):
        self._data_data_factory = data_factory

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
        """Read the current data and return it as StorageDataT."""
        raise NotImplementedError

    @abc.abstractmethod
    async def set_data(self, key: str, data: Optional[StorageDataT]) -> None:
        """
        Overwrite existing data to a new passed one.

        (!) If None was passed as ``data``, then data should become result of
        `storage._data_data_factory` and never None
        """
        raise NotImplementedError

    @abc.abstractmethod
    async def update_data(self, key: str, data: StorageDataT) -> None:
        """Merge passed data to an existing one."""
        raise NotImplementedError

    # naively implemented basic, base member methods
    async def reset_state(self, key: str) -> None:
        """Cause state reset."""
        await self.set_state(key=key, state=None)

    async def reset_data(self, key: str) -> None:
        """Cause data reset."""
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
