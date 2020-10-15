from typing import List, Optional, Tuple, Type, Union

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


class Router:
    """

    """

    __slots__ = "event", "handlers", "upper_filters"

    def __init__(
        self,
        default_event: "Optional[ET]" = None,
        *upper_filters: Filter[None],
    ):
        """
        :param default_event: Default event
        :param upper_filters:
        """
        self.event = default_event
        self.handlers: List[Type[EventHandler]] = []
        self.upper_filters = upper_filters

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
            and
            issubclass(self.event, common.EventBuilder)
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

        self.handlers.append(handler)
        return self
