import asyncio
import copy
import functools
from contextlib import contextmanager
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
    TypeVar,
    Union,
)

from telethon.client.updates import EventBuilderDict
from telethon.events import common

import _garnet.patched_events as pe
from _garnet.events.action import AfterFilterAction, NoAction, ensure_action
from _garnet.events.filter import Filter, ensure_filter
from _garnet.events.handler import (
    AsyncFunctionHandler,
    EventHandler,
    ensure_handler,
)
from _garnet.events.user_cage import KeyMakerFn, UserCage
from _garnet.loggers import events
from _garnet.vars import fsm as fsm_ctx
from _garnet.vars import handler as h_ctx
from _garnet.vars import user_and_chat as uc_ctx

if TYPE_CHECKING:
    from _garnet.client import TelegramClient
    from _garnet.storages.base import BaseStorage
    from _garnet.storages.typedef import StorageDataT

ET = TypeVar("ET", bound=common.EventBuilder)
UnwrappedIntermediateT = Callable[[Type[EventHandler], common.EventCommon], Any]

__ProxyT = TypeVar("__ProxyT")
_EventHandlerGT = Union[
    Type[EventHandler[__ProxyT]], AsyncFunctionHandler[__ProxyT],
]

FilterWithAction = Tuple[Filter[ET], Type[AfterFilterAction[ET]]]


async def check_filter(
    built: EventBuilderDict,
    filter_: Tuple[
        Filter[Optional[ET]],
        Type[AfterFilterAction[Optional[ET], Any]],
    ],
    /,
) -> bool:
    f, on_err_action = filter_

    if event := built[f.event_builder]:
        event_token = event.set_current(event)

        try:
            if await f.call(event) is True:
                return True
            else:
                asyncio.create_task(on_err_action(event, f).call())
                return False

        finally:
            event.reset_current(event_token)

    else:
        events.debug(
            f"Got event-naive filter: {filter_!r}, "
            f"calling it with default `None`"
        )
        if await f.call(None) is not True:
            asyncio.create_task(on_err_action(event, f).call())
            return False

    return True


def _map_filters(
    for_event: Optional[Type[ET]],
    filters: Tuple[Union[Filter[Optional[ET]], FilterWithAction[Optional[ET]]]],
) -> Generator[FilterWithAction, None, None]:
    for f in filters:
        if isinstance(f, tuple):
            filter_, action = f
        else:
            filter_, action = f, NoAction

        yield (
            ensure_filter(for_event, filter_),
            ensure_action(action, for_event),
        )


class Router:
    """Router table."""

    __slots__ = (
        "event",
        "_handlers",
        "upper_filters",
        "_intermediates",
        "children",
        "_cage_key_maker_f",
    )

    def __init__(
        self,
        default_event: Optional[ET] = None,
        *upper_filters: Union[
            Filter[Optional[ET]],
            FilterWithAction[Optional[ET]]
        ],
        cage_key_maker: Optional[KeyMakerFn] = None,
    ):
        """
        :param default_event: Default event
        :param upper_filters: Filters to be used to test event
        when event reaches this router
        """
        self.event = default_event
        self._handlers: List[Type[EventHandler[ET]]] = []

        if default_event is not None:
            self.upper_filters = _map_filters(default_event, upper_filters)
        else:
            self.upper_filters = upper_filters

        self._intermediates: List[UnwrappedIntermediateT] = []
        self.children: "List[Router]" = []
        self._cage_key_maker_f = cage_key_maker

    def __deepcopy__(self, memo) -> "Router":
        copied = self.__class__(
            self.event,
            *self.upper_filters,
            cage_key_maker=self._cage_key_maker_f,
        )
        copied._handlers = self._handlers
        copied._intermediates = self._intermediates
        copied.children = [
            copy.deepcopy(child, memo=memo) for child in self.children
        ]
        return copied

    def add_use(self, intermediate: UnwrappedIntermediateT) -> None:
        """
        Add async generator function to intermediates.

        :param intermediate: asynchronous generator function
        """
        self._intermediates.append(intermediate)

    def use(self) -> Callable[[UnwrappedIntermediateT], UnwrappedIntermediateT]:
        """
        Use `.use(...)` for adding router check layer

        Example:

        >>> from garnet.events import Router
        >>> router = Router()
        >>>
        >>> @router.use()
        ... async def router_intermediate(handler, event):
        ...    try:
        ...        await handler(event)
        ...    finally:
        ...         print("another iteration, another update")
        """

        def decorator(func: UnwrappedIntermediateT) -> UnwrappedIntermediateT:
            self.add_use(func)
            return func

        return decorator

    def include(self, router: "Router", /) -> "Router":
        """Include router in `Self` and return `Self`"""
        if self is router:
            raise ValueError(f"Router({router!r}) cannot include it to itself.")

        if router in self.children:
            raise ValueError(
                f"Router({router!r}) is already included for {self!r}."
            )

        self.children.append(router)
        return self

    @property
    def handlers(self) -> Generator[Type[EventHandler[ET]], None, None]:
        """Deep traverse of inner handlers."""
        for handler in self._handlers:
            yield handler
        for child in self.children:
            yield from child.handlers

    @property
    def intermediates(self) -> Generator[UnwrappedIntermediateT, None, None]:
        """Deep traverse of inner intermediates."""
        for handler in self._intermediates:
            yield handler
        for child in self.children:
            yield from child.intermediates

    @classmethod
    def _wrap_intermediates(
        cls,
        intermediates: Reversible[UnwrappedIntermediateT],
        handler: Type[EventHandler[ET]],
    ) -> Callable[[ET], Any]:
        @functools.wraps(handler)
        def mpa(event: ET) -> Any:
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

    @contextmanager
    def _contexvars_context(
        self,
        storage: "BaseStorage[StorageDataT]",
        event: ET,
        client: "TelegramClient",
        /,
    ):
        with uc_ctx.current_user_and_chat_ctx_manager(event):
            fsm_context = UserCage(
                storage,
                uc_ctx.ChatIDCtx.get(),
                uc_ctx.UserIDCtx.get(),
                self._cage_key_maker_f,
            )
            event_token = event.set_current(event)
            fsm_token = fsm_ctx.CageCtx.set(fsm_context)
            client_token = client.set_current(client)
            try:
                yield
            finally:
                event.reset_current(event_token)
                fsm_ctx.CageCtx.reset(fsm_token)
                client.reset_current(client_token)

    async def _notify_handlers(
        self,
        built: EventBuilderDict,
        storage: "BaseStorage[StorageDataT]",
        client: "TelegramClient",
        /,
    ) -> bool:
        """Shallow call."""
        for handler in self._handlers:
            if event := built[handler.__event_builder__]:
                with self._contexvars_context(
                    storage, event, client,
                ):
                    events.debug(
                        "Current context configuration: {"
                        f"CHAT_ID={uc_ctx.ChatIDCtx.get()},"
                        f"USER_ID={uc_ctx.UserIDCtx.get()},"
                        "}"
                    )

                    handler_token = None
                    try:
                        handler_token = h_ctx.HandlerCtx.set(handler)

                        for hf in handler.filters:
                            assert isinstance(hf, tuple), "Got unchecked " \
                                                          "handler, " \
                                                          "won't execute. "
                            if await check_filter(built, hf):
                                continue
                            break
                        else:
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
                        if handler_token:
                            h_ctx.HandlerCtx.reset(handler_token)

        return False

    async def notify(
        self,
        storage: "BaseStorage[StorageDataT]",
        built: EventBuilderDict,
        client: "TelegramClient",
        /,
    ) -> None:
        """Notify router and its children about update."""
        if await self._notify_filters(built) and await self._notify_handlers(
            built, storage, client
        ):
            return

        for router in self.children:
            return await router.notify(storage, built, client)

    # noinspection PyTypeChecker
    def message(
        self, *filters: "Filter[ET]",
    ) -> Callable[[_EventHandlerGT[ET]], _EventHandlerGT[ET]]:
        """Decorator for `garnet.events.NewMessage` event handlers."""

        def decorator(f_or_class: _EventHandlerGT[ET]) -> _EventHandlerGT[ET]:
            f_or_class_to_reg = ensure_handler(f_or_class, pe.NewMessage)
            self.register(f_or_class_to_reg, filters, event=pe.NewMessage)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def callback_query(
        self, *filters: "Filter[ET]",
    ) -> Callable[[_EventHandlerGT[ET]], _EventHandlerGT[ET]]:
        """Decorator for `garnet.events.CallbackQuery` event handlers."""

        def decorator(f_or_class: _EventHandlerGT[ET]) -> _EventHandlerGT[ET]:
            f_or_class_to_reg = ensure_handler(f_or_class, pe.CallbackQuery)
            self.register(f_or_class_to_reg, filters, event=pe.CallbackQuery)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def chat_action(
        self, *filters: "Union[Filter[ET], FilterWithAction[ET]]",
    ) -> Callable[[_EventHandlerGT[ET]], _EventHandlerGT[ET]]:
        """Decorator for `garnet.events.ChatAction` event handlers."""

        def decorator(f_or_class: _EventHandlerGT[ET]) -> _EventHandlerGT[ET]:
            f_or_class_to_reg = ensure_handler(f_or_class, pe.ChatAction)
            self.register(f_or_class_to_reg, filters, event=pe.ChatAction)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def message_edited(
        self, *filters: "Union[Filter[ET], FilterWithAction[ET]]",
    ) -> Callable[[_EventHandlerGT[ET]], _EventHandlerGT[ET]]:
        """Decorator for `garnet.events.MessageEdited` event handlers."""

        def decorator(f_or_class: _EventHandlerGT[ET]) -> _EventHandlerGT[ET]:
            f_or_class_to_reg = ensure_handler(f_or_class, pe.MessageEdited)
            self.register(f_or_class_to_reg, filters, event=pe.MessageEdited)
            return f_or_class

        return decorator

    def default(
        self, *filters: "Union[Filter[ET], FilterWithAction[ET]]",
    ) -> Callable[[_EventHandlerGT[ET]], _EventHandlerGT[ET]]:
        """Decorator for router's default event event handlers."""
        if self.event is None or (
            isinstance(self.event, type)
            and issubclass(self.event, common.EventBuilder)
        ):
            raise ValueError(
                "In order to use default event_builder declare it in "
                "Router(...). "
                f"Expected type {common.EventBuilder} got {type(self.event)!s}"
            )

        def decorator(f_or_class: _EventHandlerGT[ET]) -> _EventHandlerGT[ET]:
            assert self.event is not None
            f_or_class_to_reg = ensure_handler(f_or_class, self.event)
            self.register(f_or_class_to_reg, filters, event=self.event)
            return f_or_class

        return decorator

    def on(
        self,
        event_builder: "Type[common.EventBuilder]",
        /,
        *filters: "Union[Filter[ET], FilterWithAction[ET]]",
    ) -> Callable[[_EventHandlerGT[ET]], _EventHandlerGT[ET]]:
        """Decorator for a specific event-aware event handlers."""

        def decorator(f_or_class: _EventHandlerGT[ET]) -> _EventHandlerGT[ET]:
            f_or_class_to_reg = ensure_handler(f_or_class, event_builder)
            self.register(f_or_class_to_reg, filters, event=event_builder)
            return f_or_class

        return decorator

    def register(
        self,
        handler: "Type[EventHandler[ET]]",
        filters: "Tuple[Union[Filter[ET], FilterWithAction[ET]], ...]",
        event: "Type[common.EventBuilder]",
    ) -> "Router":
        """
        Entrypoint for registering event handlers on particular event builders.
        """
        handler = ensure_handler(handler, event_builder=event)
        if handler.filters:
            handler.filters += tuple(_map_filters(event, filters))
        else:
            handler.filters = tuple(_map_filters(event, filters))

        self._handlers.append(handler)
        return self

    def __str__(self) -> str:
        return (
            f"{self.__class__.__name__} stats("
            f"children={len(self.children)}, "
            f"own_handlers={len(self._handlers)}, "
            f"own_filters={len(self.upper_filters)}, "
            f"own_intermediates={len(self._intermediates)}"
            f") at {hex(id(self))}"
        )

    __repr__ = __str__
