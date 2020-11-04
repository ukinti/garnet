import contextvars
from typing import TYPE_CHECKING, Any, Type

if TYPE_CHECKING:
    from _garnet.events.handler import EventHandler


HandlerCtx: "contextvars.ContextVar[Type[EventHandler[Any]]]" = (
    contextvars.ContextVar("handler")
)
