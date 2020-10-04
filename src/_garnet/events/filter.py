from __future__ import annotations

import functools
import inspect
import operator
from typing import (
    Any,
    Awaitable,
    Callable,
    Generator,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
)

from telethon.events.common import EventBuilder

from _garnet.concurrency import to_thread

ET = TypeVar("ET")
FR = Union[bool, Awaitable[bool]]


class Filter(Generic[ET]):
    """
    Base Filter object, callback container
    """

    __slots__ = "function", "is_awaitable", "event_builder"

    def __init__(
        self,
        function: Callable[[ET], FR],
        event_builder: Optional[Type[EventBuilder]] = None,
    ):
        self.function = function
        self.is_awaitable = inspect.iscoroutinefunction(
            function
        ) or inspect.isawaitable(function)
        self.event_builder = event_builder

    def __eq__(self, value: Any) -> Filter:
        return unary_op(self, lambda filter1: operator.eq(filter1, value))

    def __ne__(self, value: Any) -> Filter:
        return unary_op(self, lambda filter1: operator.ne(filter1, value))

    def __xor__(self, filter2: Filter) -> Filter:
        return binary_op(self, filter2, operator.xor)

    def __and__(self, filter2: Filter) -> Filter:
        return binary_op(self, filter2, operator.and_)

    def __or__(self, filter2: Filter) -> Filter:
        return binary_op(self, filter2, operator.or_)

    def __invert__(self) -> Filter:
        return unary_op(self, operator.not_)

    async def call(self, e: ET, /) -> FR:
        fn = functools.partial(self.function, e)

        if self.is_awaitable:
            return await fn()
        else:
            return await to_thread(fn)

    @property
    def is_event_naive(self) -> bool:
        return self.event_builder is None


def binary_op(
    filter1: Filter[ET],
    filter2: Filter[ET],
    operator_: Callable[[bool, bool], bool],
) -> Filter:
    if (not isinstance(filter1, Filter)) | (not isinstance(filter2, Filter)):
        raise ValueError(
            f"Cannot merge non-Filter objects. {filter1!r} with {filter2!r}"
        )

    if (
        not (filter1.is_event_naive or filter2.is_event_naive)
        and filter1.event_builder != filter2.event_builder
    ):
        raise ValueError(
            "Cannot merge event-aware filters with different event_builders"
        )

    common_event_builder = filter1.event_builder

    if filter1.is_awaitable and filter2.is_awaitable:

        async def func(event):
            return operator_(
                await filter1.function(event), await filter2.function(event),
            )

        return Filter(function=func, event_builder=common_event_builder)

    elif filter1.is_awaitable ^ filter2.is_awaitable:
        async_func = filter1 if filter1.is_awaitable else filter2
        sync_func = filter2 if async_func == filter1 else filter1

        async def func(event):
            return operator_(
                await async_func.function(event), sync_func.function(event)
            )

        return Filter(function=func, event_builder=common_event_builder)

    def func(event):
        return operator_(filter1.function(event), filter2.function(event))

    return Filter(function=func, event_builder=common_event_builder)


def unary_op(filter1: Filter[ET], operator_: Callable[[bool], bool]) -> Filter:
    if filter1.is_awaitable:

        async def func(event):
            return operator_(await filter1.function(event))

        return Filter(function=func, event_builder=filter1.event_builder)

    def func(event):
        return operator_(filter1.function(event))

    return Filter(function=func, event_builder=filter1.event_builder)


def ensure_filters(
    event_builder: Optional[Type[EventBuilder]],
    filters: Tuple[Union[Filter[ET], Callable[[ET], bool]], ...],
) -> Generator[Filter, None, None]:
    for filter_ in filters:
        if isinstance(filter_, Filter):
            if not filter_.event_builder:
                filter_.event_builder = event_builder
            yield filter_
        else:
            yield Filter(function=filter_, event_builder=event_builder)


__all__ = (
    "Filter",
    "ensure_filters",
)
