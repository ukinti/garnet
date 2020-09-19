import abc
from typing import Awaitable, Callable, Generic, Tuple, Type, TypeVar

from telethon.events.common import EventBuilder

from garnet.events.filter import Filter

ET = TypeVar("ET")
AsyncFunctionHandler = Callable[[ET], Awaitable[None]]


class EventHandler(Generic[ET], abc.ABC):
    filters: Tuple[Filter, ...]

    @property
    @abc.abstractmethod
    def __event_builder__(self) -> "Type[EventBuilder]":
        pass

    def __init__(self, e: ET):
        self.e = e

    @abc.abstractmethod
    async def handle(self):
        pass

    def __await__(self):
        return self.handle().__await__()


def ensure_handler(
    callable_: AsyncFunctionHandler[ET], event_builder: "Type[EventBuilder]",
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
