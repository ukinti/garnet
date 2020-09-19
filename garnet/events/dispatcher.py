from typing import Optional, Sequence, Tuple

from telethon.client.updates import EventBuilderDict

from garnet.events.filter import Filter
from garnet.events.router import Router, SomeEventT
from garnet.storages.base import BaseStorage, FSMContext
from garnet.vars import fsm
from garnet.vars import user_and_chat as uc


async def _solve_filters(
    e: Optional[SomeEventT], /, filters: Tuple[Filter, ...],
) -> bool:
    for filter_ in filters:
        if await filter_.call(e) is not True:
            return False

    return True


async def _check_then_call_router_handlers(
    built: EventBuilderDict, /, router: Router, storage: BaseStorage,
) -> bool:
    for handler in router.handlers:
        if event := built[handler.__event_builder__]:
            with uc.current_user_and_chat_ctx_manager(event):
                fsm_token = fsm.State.set(
                    FSMContext(storage, chat=uc.ChatID.get(), user=uc.UserID.get())
                )

                try:
                    if await _solve_filters(event, handler.filters):
                        await handler(event)
                        return True
                finally:
                    fsm.State.reset(fsm_token)

    return False


class EventDispatcher:
    __slots__ = "_storage", "_routers"

    def __init__(
        self, storage: BaseStorage, routers: Sequence[Router],
    ):
        self._storage = storage
        self._routers = routers

    async def handle(self, built: EventBuilderDict, /):
        for router in self._routers:
            if await _solve_filters(
                None, router.upper_filters
            ) and await _check_then_call_router_handlers(built, router, self._storage):
                break
