import functools
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    Generator,
    List,
    Optional,
    Reversible,
    Tuple,
    Type,
    Union,
)

from telethon.client.updates import EventBuilderDict
from telethon.events import common

import _garnet.patched_events as pe
from _garnet.events.filter import Filter, ensure_filters
from _garnet.events.fsm_context import FSMContext
from _garnet.events.handler import EventHandler, ensure_handler
from _garnet.loggers import events
from _garnet.vars import fsm as fsm_ctx
from _garnet.vars import handler as h_ctx
from _garnet.vars import user_and_chat as uc_ctx

if TYPE_CHECKING:
    from _garnet.client import TelegramClient
    from _garnet.storages.base import BaseStorage


ET = Union[common.EventBuilder, Type[common.EventBuilder]]
UnwrappedIntermediateT = Callable[[Type[EventHandler], common.EventCommon], Any]


async def check_filter(
    built: EventBuilderDict, filter_: Filter[Optional[ET]],
) -> bool:
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


class Router:
    """
    Router class
    """

    __slots__ = (
        "event",
        "_handlers",
        "upper_filters",
        "_intermediates",
        "children",
    )

    def __init__(
        self,
        default_event: "Optional[ET]" = None,
        *upper_filters: Filter[None],
    ):
        """
        :param default_event: Default event
        :param upper_filters: Filters to be used to test event
        when event reaches this router
        """
        self.event = default_event
        self._handlers: List[Type[EventHandler]] = []
        self.upper_filters = upper_filters
        self._intermediates: List[UnwrappedIntermediateT] = []
        self.children: "List[Router]" = []

    def add_use(self, intermediate: UnwrappedIntermediateT) -> None:
        """
        Add async generator function to intermediates.

        :param intermediate: asynchronous generator function
        """
        self._intermediates.append(intermediate)

    def use(self):
        """
        Use `.use(...)` for adding router check layer

        Example:

        >>> @router.use()
        ... async def router_intermediate(handler, event):
        ...    async with my_shiny_database.open_txn():
        ...        await handler(event)
        """

        def decorator(func: UnwrappedIntermediateT) -> UnwrappedIntermediateT:
            self.add_use(func)
            return func

        return decorator

    def include(self, router: "Router") -> "Router":
        if self is router:
            raise ValueError(f"Router({router!r}) cannot include it to itself.")

        if router in self.children:
            raise ValueError(
                f"Router({router!r}) is already included for {self!r}."
            )

        self.children.append(router)
        return self

    @property
    def handlers(self) -> Generator[Type[EventHandler], None, None]:
        for handler in self._handlers:
            yield handler
        for child in self.children:
            yield from child.handlers

    @property
    def intermediates(
        self,
    ) -> Generator[Type[UnwrappedIntermediateT], None, None]:
        for handler in self._intermediates:
            yield handler
        for child in self.children:
            yield from child.intermediates

    @classmethod
    def _wrap_intermediates(
        cls,
        intermediates: Reversible[UnwrappedIntermediateT],
        handler: Type[EventHandler],
    ) -> Callable[[ET], Any]:
        @functools.wraps(handler)
        def mpa(event) -> Any:
            return handler(event)

        for inter in reversed(intermediates):
            mpa = functools.partial(inter, mpa)
        return mpa

    async def _notify_filters(self, built: EventBuilderDict) -> bool:
        """Shallow call"""
        for filter_ in self.upper_filters:
            if not await check_filter(built, filter_):
                return False
        return True

    async def _notify_handlers(
        self,
        built: EventBuilderDict,
        storage: "BaseStorage",
        client: "TelegramClient",
    ) -> bool:
        """Shallow call."""
        for handler in self._handlers:
            if event := built[handler.__event_builder__]:
                with uc_ctx.current_user_and_chat_ctx_manager(event):
                    fsm_context = FSMContext(
                        storage,
                        chat=uc_ctx.ChatIDCtx.get(),
                        user=uc_ctx.UserIDCtx.get(),
                    )
                    event_token = event.set_current(event)
                    fsm_token = fsm_ctx.StateCtx.set(fsm_context)
                    client_token = client.set_current(client)
                    handler_token = h_ctx.HandlerCtx.set(handler)

                    # noinspection PyUnreachableCode
                    if __debug__:
                        events.debug(
                            "Current context configuration: {"
                            f"CHAT_ID={uc_ctx.ChatIDCtx.get()},"
                            f"USER_ID={uc_ctx.UserIDCtx.get()},"
                            "}"
                        )

                    try:
                        for hf in handler.filters:
                            if await check_filter(built, hf):
                                events.debug(
                                    f"Executing handler({handler!r}) after it "
                                    f"passed relevance test"
                                )
                                await self._wrap_intermediates(
                                    self._intermediates, handler,
                                )(event)
                                return True

                    except pe.StopPropagation:
                        events.debug(
                            f"Stopping propagation for all next handlers "
                            f"after {handler!r}"
                        )
                        break

                    except pe.SkipHandler:
                        events.debug(f"Skipping handler({handler!r}) execution")
                        continue

                    finally:
                        event.reset_current(event_token)
                        fsm_ctx.StateCtx.reset(fsm_token)
                        client.reset_current(client_token)
                        h_ctx.HandlerCtx.reset(handler_token)

        return False

    async def notify(
        self,
        storage: "BaseStorage",
        built: EventBuilderDict,
        client: "TelegramClient",
    ) -> None:
        if await self._notify_filters(built) and await self._notify_handlers(
            built, storage, client
        ):
            return

        for router in self.children:
            return await router.notify(storage, built, client)

    # noinspection PyTypeChecker
    def message(self, *filters: "Filter[ET]"):
        """Decorator for `garnet.events.NewMessage` event handlers."""

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=pe.NewMessage)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def callback_query(self, *filters: "Filter[ET]"):
        """Decorator for `garnet.events.CallbackQuery` event handlers."""

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=pe.CallbackQuery)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def chat_action(self, *filters: "Filter[ET]"):
        """Decorator for `garnet.events.ChatAction` event handlers."""

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=pe.ChatAction)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def message_edited(self, *filters: "Filter[ET]"):
        """Decorator for `garnet.events.MessageEdited` event handlers."""

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=pe.MessageEdited)
            return f_or_class

        return decorator

    def default(self, *filters: "Filter[ET]"):
        """Decorator for router's default event event handlers."""
        if self.event is None or (
            isinstance(self.event, type)
            and issubclass(self.event, common.EventBuilder)
        ):
            raise ValueError(
                "In order to use default event_builder declare it in "
                "Router(...). "
                f"Expected type {common.EventBuilder} got {type(self.event)!r}"
            )

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=self.event)
            return f_or_class

        return decorator

    def on(
        self,
        event_builder: "Type[common.EventBuilder]",
        /,
        *filters: "Filter[ET]",
    ):
        """Decorator for a specific event-aware event handlers."""

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=event_builder)
            return f_or_class

        return decorator

    def register(
        self,
        handler: "EventHandler[ET]",
        filters: "Tuple[Filter, ...]",
        event: "Type[common.EventBuilder]",
    ) -> "Router":
        """
        Entrypoint for registering event handlers on particular event builders.
        """
        handler = ensure_handler(handler, event_builder=event)
        if handler.filters:
            handler.filters += tuple(ensure_filters(event, filters))
        else:
            handler.filters = tuple(ensure_filters(event, filters))

        self._handlers.append(handler)
        return self
