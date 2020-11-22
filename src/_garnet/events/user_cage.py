from typing import Any, Callable, Dict, Generic, Mapping, Optional, Union

from _garnet.filters.state import M
from _garnet.storages.base import BaseStorage
from _garnet.storages.typedef import StorageDataT

KeyMakerFn = Callable[[Optional[int], Optional[int]], str]


def _default_key_maker(
    chat_id: Optional[int] = None, user_id: Optional[int] = None, /,
) -> str:
    if chat_id is None and user_id is None:
        raise ValueError(
            "`user_id` or `chat_id` parameter is required "
            "but neither is provided!"
        )

    if user_id is None and chat_id is not None:
        user_id = chat_id
    elif user_id is not None and chat_id is None:
        chat_id = user_id
    return f"{chat_id}:{user_id}"


class UserCage(Generic[StorageDataT]):
    """
    UserCage is "cage" for a particular user in chat.
    That stores user's state and can also be used to store user related date
    """

    __slots__ = "key", "storage"

    def __init__(
        self,
        storage: BaseStorage[StorageDataT],
        chat_id: Optional[int],
        user_id: Optional[int],
        key_maker: Optional[KeyMakerFn],
        /,
    ):
        if key_maker is None:
            key_maker = _default_key_maker

        self.key = key_maker(chat_id, user_id)
        self.storage = storage

    async def get_state(self) -> Optional[str]:
        """Get user's state."""
        return await self.storage.get_state(self.key)

    async def get_data(self) -> Optional[StorageDataT]:
        """Get data associated with user."""
        return await self.storage.get_data(self.key)

    async def update_data(
        self, data: Optional[StorageDataT] = None, /, **kwargs: Any,
    ) -> None:
        """Update user's data"""
        if data is not None and not isinstance(data, Mapping):
            raise ValueError(
                "type for `data` is expected to be a subtype "
                "of `collections.Mapping`"
            )

        temp_data: Dict[str, Any] = {}

        if isinstance(data, Mapping):
            temp_data.update(data)

        temp_data.update(**kwargs)

        await self.storage.update_data(self.key, data=temp_data)  # type: ignore

    async def set_state(self, state: Optional[Union[M, str]] = None) -> None:
        """Set user's current state, state can be M(ember) of a state group."""
        if isinstance(state, M):
            state_name = state.name
        else:
            state_name = state

        await self.storage.set_state(self.key, state=state_name)

    async def set_data(self, data: Optional[StorageDataT] = None) -> None:
        """Rewrite user associated data."""
        await self.storage.set_data(self.key, data=data)

    async def reset_state(self) -> None:
        """Reset user's state."""
        await self.storage.reset_state(self.key)

    async def reset_data(self) -> None:
        """Reset user's data"""
        await self.storage.reset_data(self.key)

    async def free(self) -> None:
        """
        Set user **free**

        >>> from garnet.events import UserCage
        >>> from garnet.storages import DictStorage
        >>> cage = UserCage(DictStorage(), 0x1, 0x2)
        >>> await cage.update_data(abc=123)
        >>> await cage.set_state("some")
        >>> assert await cage.get_data() == {"abc": 123}
        >>> assert await cage.get_state() == "some"
        >>> await cage.free()
        >>> assert await cage.get_state() is None
        >>> assert await cage.get_data() is None
        """
        await self.storage.reset(self.key)
