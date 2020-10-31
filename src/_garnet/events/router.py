from typing import Any, Callable, List, Optional, Tuple, Type, Union, Generator

from telethon.events import common

from _garnet.events.filter import Filter, ensure_filters
from _garnet.events.handler import EventHandler, ensure_handler
from _garnet.patched_events import (
    CallbackQuery,
    ChatAction,
    MessageEdited,
    NewMessage,
)

ET = Union[common.EventBuilder, Type[common.EventBuilder]]
UnwrappedIntermediateT = Callable[[Type[EventHandler], common.EventCommon], Any]


class Router:
    """
    Router class
    """

    __slots__ = (
        "event", "_handlers", "upper_filters", "_intermediates", "children",
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

    # noinspection PyTypeChecker
    def message(self, *filters: "Filter[ET]"):
        """Decorator for `garnet.events.NewMessage` event handlers."""

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=NewMessage)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def callback_query(self, *filters: "Filter[ET]"):
        """Decorator for `garnet.events.CallbackQuery` event handlers."""

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=CallbackQuery)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def chat_action(self, *filters: "Filter[ET]"):
        """Decorator for `garnet.events.ChatAction` event handlers."""

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=ChatAction)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def message_edited(self, *filters: "Filter[ET]"):
        """Decorator for `garnet.events.MessageEdited` event handlers."""

        def decorator(f_or_class):
            self.register(f_or_class, filters, event=MessageEdited)
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
