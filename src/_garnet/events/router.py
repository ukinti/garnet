from typing import TYPE_CHECKING, List, Optional, Tuple, Type, TypeVar, Union

from _garnet.events.filter import Filter, ensure_filters
from _garnet.events.handler import EventHandler, ensure_handler
from _garnet.patched_events import (
    CallbackQuery,
    ChatAction,
    MessageEdited,
    NewMessage,
)

if TYPE_CHECKING:
    from telethon.events import common

    ET = Union[common.EventBuilder, Type[common.EventBuilder]]


SomeEventT = TypeVar("SomeEventT")


class Router:
    __slots__ = "event", "handlers", "upper_filters"

    def __init__(
        self, default_event: "Optional[ET]", *upper_filters: Filter[None]
    ):
        """
        BaseRouter
        :param frozen: While registering router it can be frozen once.
        """
        self.event = default_event
        self.handlers: List[Type[EventHandler]] = []
        self.upper_filters = upper_filters

    # noinspection PyTypeChecker
    def message(self, *filters: Filter[ET]):
        def decorator(f_or_class):
            self.register(f_or_class, filters, event=NewMessage)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def callback_query(self, *filters: Filter[ET]):
        def decorator(f_or_class):
            self.register(f_or_class, filters, event=CallbackQuery)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def chat_action(self, *filters: Filter[ET]):
        def decorator(f_or_class):
            self.register(f_or_class, filters, event=ChatAction)
            return f_or_class

        return decorator

    # noinspection PyTypeChecker
    def message_edited(self, *filters: Filter[ET]):
        def decorator(f_or_class):
            self.register(f_or_class, filters, event=MessageEdited)
            return f_or_class

        return decorator

    def on(
        self,
        event_builder: "Type[common.EventBuilder]",
        /,
        *filters: Filter[ET],
    ):
        def decorator(f_or_class):
            self.register(f_or_class, filters, event=event_builder)
            return f_or_class

        return decorator

    def register(
        self,
        handler,
        filters: Tuple[Filter, ...],
        event: "Type[common.EventBuilder]",
    ) -> "Router":
        handler = ensure_handler(handler, event_builder=event)
        if handler.filters:
            handler.filters += tuple(ensure_filters(filters))
        else:
            handler.filters = tuple(ensure_filters(filters))

        self.handlers.append(handler)
        return self
