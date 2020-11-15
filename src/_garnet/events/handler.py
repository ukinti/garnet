import abc
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from telethon.events.common import EventBuilder

from _garnet.events.filter import Filter

ET = TypeVar("ET")
AsyncFunctionHandler = Callable[[ET], Awaitable[None]]


class EventHandler(Generic[ET], abc.ABC):
    """
    Base class-based event handler

    Usage example::
    from telethon import custom
    from garnet import handler, filters, events

    def sqrt_f(n: float, /):
            return n ** 0.5

    class SqrtHandler(handler.EventHandler[custom.Message]):
        __event_builder__ = events.NewMessage
        filters = (filters.text.can_be_float(), )

        async def handle(self) -> None:
            rooted = sqrt_f(float(self.e.raw_text))
            self.e.reply(f"{:.6f}")

    """

    filters: Tuple[Filter[ET], ...]

    @property
    @abc.abstractmethod
    def __event_builder__(self) -> "Type[EventBuilder]":
        pass

    def __init__(self, e: ET):
        self.e = e

    @abc.abstractmethod
    async def handle(self) -> Any:
        pass

    def __await__(self) -> Any:
        return self.handle().__await__()


def ensure_handler(
    callable_: Union[AsyncFunctionHandler[ET], Type[EventHandler[ET]]],
    event_builder: "Type[EventBuilder]",
) -> Type[EventHandler[ET]]:
    if isinstance(callable_, type) and issubclass(callable_, EventHandler):
        return callable_

    else:
        # noinspection PyTypeChecker
        return type(
            callable_.__name__,
            (EventHandler,),
            {
                "__doc__": callable_.__doc__,
                "__event_builder__": event_builder,
                "filters": (),
                "handle": lambda self: callable_(self.e),
            },
        )
