import abc
from typing import Any, Awaitable, Callable, Generic, Type, TypeVar, Union

from telethon.events.common import EventBuilder

ET = TypeVar("ET")
AsyncFunction = Callable[[ET, Any], Awaitable[None]]


class AfterFilterAction(Generic[ET], abc.ABC):
    """
    Base class-based action

    Usage example::
    from telethon import custom
    from garnet import action, events

    Usage::
        class AfterWrongIntAction(action.AfterFilterAction[custom.Message]):
            async def call(self) -> None:
                await self.e.reply(f"Hey! {self.e.raw_text} can not be int!")

    """

    @property
    @abc.abstractmethod
    def __event_builder__(self) -> "Type[EventBuilder]":
        pass

    def __init__(self, e: ET, emitted_from: Any):
        self.e = e
        self.emitted_from = emitted_from

    @abc.abstractmethod
    async def call(self) -> Any:
        pass

    def __await__(self) -> Any:
        return self.call().__await__()


def ensure_action(
    callable_: Union[AsyncFunction[ET], Type[AfterFilterAction[ET]]],
    event_builder: "Type[EventBuilder]",
) -> Type[AfterFilterAction[ET]]:
    if callable_ is NoAction:
        return callable_

    if isinstance(callable_, type) and issubclass(callable_, AfterFilterAction):
        return callable_

    else:
        # noinspection PyTypeChecker
        return type(
            callable_.__name__,
            (AfterFilterAction,),
            {
                "__doc__": callable_.__doc__,
                "__event_builder__": event_builder,
                "call": lambda self: callable_(self.e, self.emitted_from),
            },
        )


class NoAction(AfterFilterAction):
    __event_builder__ = None

    async def call(self) -> Any:
        return None
