from __future__ import annotations
import operator
import inspect
from typing import Callable, Any


class Filter:
    """
    Base Filter object, callback container
    """

    def __init__(
        self, function: Callable, requires_context: bool = False, state_op: bool = False
    ):
        if isinstance(function, Filter):
            self.__name__ = function.__qualname__
            self.function = function.function
            self.awaitable = function.awaitable
            self.requires_context = function.requires_context
            self.key_maker = function.key_maker

        else:
            name = function.__qualname__
            if name == "<lambda>":
                name = f"{function!s}"

            self.__name__ = f"Garnet:Filter:{name}"

            self.function = function
            self.awaitable = inspect.iscoroutinefunction(
                function
            ) or inspect.isawaitable(function)
            self.requires_context = requires_context

        self.key_maker = None

        self.__qualname__ = self.__name__
        self.state_op = state_op

    @classmethod
    def from_def_state(cls, state_op: bool):
        return lambda function, requires_context=False: cls(
            function, requires_context, state_op
        )

    def __eq__(self, value: Any) -> Filter:
        return _singfilter(self, lambda filter1: operator.eq(filter1, value))

    def __ne__(self, value: Any) -> Filter:
        return _singfilter(self, lambda filter1: operator.ne(filter1, value))

    def __xor__(self, filter2: Filter) -> Filter:
        return _compose_filter(self, filter2, operator.xor)

    def __and__(self, filter2: Filter) -> Filter:
        return _compose_filter(self, filter2, operator.and_)

    def __or__(self, filter2: Filter) -> Filter:
        return _compose_filter(self, filter2, operator.or_)

    def __invert__(self) -> Filter:
        return _singfilter(self, operator.not_)


def _compose_filter(filter1: Filter, filter2: Filter, operator_) -> Filter:
    if (not isinstance(filter1, Filter)) | (not isinstance(filter2, Filter)):
        raise ValueError(
            f"Cannot compare non-Filter object with Filter, "
            f"got filter1={filter1.__qualname__} "
            f"operator={operator_.__qualname__} "
            f"filter2={filter2.__qualname__}"
        )

    result = Filter.from_def_state(filter1.state_op | filter2.state_op)
    if (filter1.awaitable & filter2.awaitable) & (
        filter1.requires_context & filter2.requires_context
    ):

        async def func(event, context):
            return operator_(
                await filter1.function(event, context),
                await filter2.function(event, context),
            )

        return result(func, True)

    elif (filter1.awaitable ^ filter2.awaitable) & (
        filter1.requires_context ^ filter2.requires_context
    ):
        # as told, passing context to sync function has no sense
        # so awaitable function here is which requires context
        is_f1_async = filter1.awaitable or filter1.requires_context
        async_func = filter1 if is_f1_async else filter2
        sync_func = filter2 if is_f1_async else filter1

        async def func(event, context):
            return operator_(
                await async_func.function(event, context), sync_func.function(event)
            )

        return result(func, True)

    elif filter1.awaitable ^ filter2.awaitable:
        async_func = filter1 if filter1.awaitable else filter2
        sync_func = filter2 if async_func == filter1 else filter1

        async def func(event):
            return operator_(
                await async_func.function(event), sync_func.function(event)
            )

        return result(func)

    def func(event):
        return operator_(filter1.function(event), filter2.function(event))

    return result(func)


def _singfilter(filter1: Filter, operator_) -> Filter:
    result = Filter.from_def_state(filter1.state_op)

    if filter1.awaitable | filter1.requires_context:
        if filter1.requires_context:

            async def func(event, context):
                return operator_(await filter1.function(event, context))

            return result(func, requires_context=True)

        async def func(event):
            return operator_(await filter1.function(event))

        return result(func)

    def func(event):
        return operator_(filter1.function(event))

    return result(func)


__all__ = ("Filter",)
