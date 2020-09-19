from typing import Sequence, Tuple

from telethon.client.updates import EventBuilderDict

from _garnet.client import TelegramClient
from _garnet.events.filter import Filter
from _garnet.events.fsm_context import FSMContext
from _garnet.events.router import Router
from _garnet.storages.base import BaseStorage
from _garnet.vars import fsm
from _garnet.vars import user_and_chat as uc


async def _solve_filters(built: EventBuilderDict, /, filters: Tuple[Filter, ...],) -> bool:
    for filter_ in filters:
        event = built[filter_.event_builder]

        if not event.resolved:
            await event.resolve()

        event_token = event.set_current(event)

        try:
            if await filter_.call(event) is not True:
                return False
        finally:
            event.reset_current(event_token)

    return True


async def _check_then_call_router_handlers(
    built: EventBuilderDict, /, router: Router, storage: BaseStorage, client: TelegramClient,
) -> bool:
    for handler in router.handlers:
        if event := built[handler.__event_builder__]:
            with uc.current_user_and_chat_ctx_manager(event):
                fsm_context = FSMContext(storage, chat=uc.ChatID.get(), user=uc.UserID.get())
                event_token = event.set_current(event)
                fsm_token = fsm.StateCtx.set(fsm_context)
                client_token = client.set_current(client)

                try:
                    if await _solve_filters(event, handler.filters):
                        await handler(event)
                        return True
                finally:
                    event.reset_current(event_token)
                    fsm.StateCtx.reset(fsm_token)
                    client.reset_current(client_token)

    return False


class EventDispatcher:
    __slots__ = "storage", "_routers"

    def __init__(
        self, storage: BaseStorage, routers: Sequence[Router],
    ):
        self.storage = storage
        self._routers = routers

    async def handle(self, built: EventBuilderDict, client: TelegramClient, /):
        for router in self._routers:
            ok = await _solve_filters(built, router.upper_filters)
            if ok:
                ok = await _check_then_call_router_handlers(built, router, self.storage, client)
                if ok:
                    break


__all__ = ("EventDispatcher",)
