import inspect
from typing import Callable, List


class Filter:
    def __init__(
        self,
        function: Callable,
        requires_context: bool = False,
    ):
        if isinstance(function, Filter):
            self.function = function.function
            self.awaitable = function.awaitable
            self.requires_context = function.requires_context

        else:
            self.function = function
            self.awaitable = False
            self.requires_context = requires_context

            if inspect.iscoroutinefunction(function) or inspect.isawaitable(function):
                self.awaitable = True


class CurrentState:
    @classmethod
    def exact(cls, state: str, reverse: bool = False) -> Filter:
        async def _f(*_, context):
            if reverse:
                return (await context.get_state()) != state
            return (await context.get_state()) == state

        return Filter(_f, requires_context=True)

    @classmethod
    def between(cls, states: List[str]) -> Filter:
        async def _f(*_, context):
            return (await context.get_state()) in states

        return Filter(_f, requires_context=True)

    @classmethod
    def equal(cls, state: str) -> Filter:
        return cls.exact(state)

    @classmethod
    def not_equal(cls, state: str) -> Filter:
        return cls.exact(state, reverse=True)

    @classmethod
    def any(cls) -> Filter:
        return Filter(lambda *ignore: True)
