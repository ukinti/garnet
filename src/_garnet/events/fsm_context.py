from typing import Any, Dict, Optional

from _garnet.filters.state import M
from _garnet.storages.base import BaseStorage


class FSMContext:
    def __init__(
        self, storage: BaseStorage, chat: Optional[int], user: Optional[int]
    ):
        self.storage = storage
        self.chat, self.user = self.storage.check_address(chat=chat, user=user)

    async def get_state(self) -> Optional[str]:
        return await self.storage.get_state(chat=self.chat, user=self.user)

    async def get_data(self) -> Dict[str, Any]:
        return await self.storage.get_data(chat=self.chat, user=self.user)

    async def update_data(
        self, data: Optional[Dict[str, Any]] = None, **kwargs: Any
    ) -> None:
        await self.storage.update_data(
            chat=self.chat, user=self.user, data=data, **kwargs
        )

    async def set_state(self, state: Optional[M] = None) -> None:
        if state is not None:
            state = state.name

        await self.storage.set_state(
            chat=self.chat, user=self.user, state=state
        )

    async def set_data(self, data: Optional[Dict[str, Any]] = None) -> None:
        await self.storage.set_data(chat=self.chat, user=self.user, data=data)

    async def reset_state(self, with_data: bool = True) -> None:
        await self.storage.reset_state(
            chat=self.chat, user=self.user, with_data=with_data
        )

    async def reset_data(self) -> None:
        await self.storage.reset_data(chat=self.chat, user=self.user)

    async def finish(self) -> None:
        await self.storage.finish(chat=self.chat, user=self.user)
