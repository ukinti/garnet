import functools
from typing import Any, Sequence, Optional, Tuple, Type, TypeVar, Callable

from telethon.client.updates import EventBuilderDict

from _garnet.client import TelegramClient
from _garnet.events.filter import Filter
from _garnet.events.fsm_context import FSMContext
from _garnet.events.handler import EventHandler
from _garnet.events.router import Router
from _garnet.loggers import events
from _garnet.patched_events import SkipHandler, StopPropagation
from _garnet.storages.base import BaseStorage
from _garnet.storages.memory import MemoryStorage
from _garnet.vars import fsm
from _garnet.vars import user_and_chat as uc

_T = TypeVar("_T")


def _wrap_intermediates(intermediates: Tuple, handler: Type[EventHandler]):
    @functools.wraps(handler)
    def mpa(event) -> Any:
        return handler(event)

    for inter in reversed(intermediates):
        mpa = functools.partial(inter, mpa)
    return mpa


async def _solve_filters(
    built: EventBuilderDict, /, filters: Tuple[Filter, ...],
) -> bool:
    for filter_ in filters:
        if event := built[filter_.event_builder]:
            event_token = event.set_current(event)

            try:
                if await filter_.call(event) is not True:
                    return False
            finally:
                event.reset_current(event_token)

        else:
            events.debug(
                f"Got event-naive filter: {filter_!r}, "
                f"calling it with default `None`"
            )
            if await filter_.call(None) is not True:
                return False

    return True


async def _check_then_call_router_handlers(
    built: EventBuilderDict,
    /,
    router: Router,
    storage: BaseStorage,
    client: TelegramClient,
) -> bool:
    for handler in router.handlers:
        if event := built[handler.__event_builder__]:
            with uc.current_user_and_chat_ctx_manager(event):

                fsm_context = FSMContext(
                    storage, chat=uc.ChatIDCtx.get(), user=uc.UserIDCtx.get(),
                )
                event_token = event.set_current(event)
                fsm_token = fsm.StateCtx.set(fsm_context)
                client_token = client.set_current(client)

                # noinspection PyUnreachableCode
                if __debug__:
                    events.debug(
                        "Current context configuration: {"
                        f"CHAT_ID={uc.ChatIDCtx.get()},"
                        f"USER_ID={uc.UserIDCtx.get()},"
                        "}"
                    )

                try:
                    if await _solve_filters(built, handler.filters):
                        events.debug(
                            f"Executing handler({handler!r}) after it "
                            f"passed relevance test"
                        )
                        await _wrap_intermediates(
                            tuple(router.intermediates), handler,
                        )(event)
                        return True

                except StopPropagation:
                    events.debug(
                        f"Stopping propagation for all next handlers "
                        f"after {handler!r}"
                    )
                    break

                except SkipHandler:
                    events.debug(f"Skipping handler({handler!r}) execution")
                    continue

                finally:
                    event.reset_current(event_token)
                    fsm.StateCtx.reset(fsm_token)
                    client.reset_current(client_token)

    return False


def make_handle(
    routers: Sequence[Router],
    storage: Optional[BaseStorage] = None,
    *,
    no_storage_warning: bool = False,
) -> Tuple[BaseStorage, Callable]:
    if storage is None:
        if not no_storage_warning:
            # todo warn user that default memory storage is being used
            pass

        storage = MemoryStorage()

    async def handle(built: EventBuilderDict, client: TelegramClient, /):
        for router in routers:
            ok = await _solve_filters(built, router.upper_filters)
            if ok:
                ok = await _check_then_call_router_handlers(
                    built, router, storage, client
                )
                if ok:
                    break

    return storage, handle


__all__ = ("make_handle",)
