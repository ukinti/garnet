from __future__ import annotations

import functools
import inspect
import operator
from typing import (
    Awaitable,
    Callable,
    Generator,
    Generic,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    cast,
)

from telethon.events.common import EventBuilder

from _garnet.concurrency import to_thread

ET = TypeVar("ET")
FR = Union[bool, Awaitable[bool]]


class Filter(Generic[ET]):
    """
    Base Filter object, single callback container

    Example:

    >>> from typing import Optional
    >>> from garnet import events
    >>> from garnet.filters import Filter
    >>>
    >>> async def filter_function(e: Optional[events.NewMessage.Event]) -> bool:
    ...     return False
    ...
    >>> naive = Filter(filter_function)
    >>> aware = Filter(filter_function, events.NewMessage)
    >>> non_async_naive = Filter(lambda _: True)
    >>>
    >>> assert naive.is_event_naive and naive.is_awaitable
    >>> assert not aware.is_event_naive and aware.is_awaitable
    >>> assert non_async_naive.is_event_naive
    >>> assert not non_async_naive.is_awaitable

    """

    __slots__ = "function", "is_awaitable", "event_builder"

    def __init__(
        self,
        function: Callable[[ET], FR],
        event_builder: Optional[Type[EventBuilder]] = None,
    ) -> None:
        """
        :param function: A single parameter function (Optional[EventType])
        that must return boolean (True/False) value
        (Can be `async def` defined function)
        :param event_builder: telethon's EventBuilder inheritor.
        Mostly you don't want to interact with this parameter.
        """

        self.function = function
        self.is_awaitable = inspect.iscoroutinefunction(
            function
        ) or inspect.isawaitable(function)
        self.event_builder = event_builder

    def __xor__(self, filter2: Filter[ET]) -> Filter[ET]:
        """
        XOR test of two filters' results.
        Usage: `Filter(...) ^ Filter(...)`

        :param filter2: must be type of merge'able filter
        :return: newly composed filter

        Example:

        >>> from garnet.events import Router
        >>> from garnet.filters import Filter
        >>> router = Router()
        >>>
        >>> @router.message(Filter(lambda _: False) ^ Filter(lambda _: False))
        >>> async def never_gonna_work(event): pass
        ...
        >>>
        """

        return binary_op(self, filter2, operator.xor)

    def __and__(self, filter2: Filter[ET]) -> Filter[ET]:
        """
        AND test of two filters' results.
        Usage: `Filter(...) & Filter(...)`

        :param filter2: must be type of "mergable" filter
        :return: newly composed filter
        """

        return binary_op(self, filter2, operator.and_)

    def __or__(self, filter2: Filter[ET]) -> Filter[ET]:
        """
        OR test of two filters' results.
        Usage: `Filter(...) | Filter(...)`

        :param filter2: must be type of "mergable" filter
        :return: newly composed filter
        """

        return binary_op(self, filter2, operator.or_)

    def __invert__(self) -> Filter[ET]:
        """
        INVERSION (actually, NEGATION) operation for a filter.
        Usage: `~Filter(...)`

        :return: newly composed filter
        """

        return unary_op(self, operator.not_)

    async def call(self, e: ET, /) -> bool:
        """
        Call functor with type contracted parameter.
        If the initial function is async, call result will be awaited

        :param e: Some data
        :return:
        """
        fn = cast(Callable[[], FR], functools.partial(self.function, e))

        if self.is_awaitable:
            fn = cast(Callable[[], Awaitable[bool]], fn)
            return await fn()
        else:
            fn = cast(Callable[[], bool], fn)
            return await to_thread(fn)

    @property
    def is_event_naive(self) -> bool:
        """Test if the Filter's got any `event_builder`"""
        return self.event_builder is None

    def __str__(self) -> str:
        return f"Filter on top of ({self.function.__name__}) at {hex(id(self))}"

    __repr__ = __str__


def binary_op(
    filter1: Filter[ET],
    filter2: Filter[ET],
    operator_: Callable[[bool, bool], bool],
) -> Filter[ET]:
    """Merge two filter and apply `operator_` function."""

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

    async def func(event: ET) -> bool:
        return operator_(await filter1.call(event), await filter2.call(event),)

    func.__name__ = (
        f"Merged({filter1.function.__name__}+{filter2.function.__name__})"
    )

    # noinspection PyUnreachableCode
    if __debug__:
        func.__doc__ = (
            f"Merged:\nA: {filter1.function.__name__}"
            f"\nB: {filter2.function.__name__}"
        )

    return Filter(function=func, event_builder=common_event_builder)


def unary_op(
    filter1: Filter[ET], operator_: Callable[[bool], bool],
) -> Filter[ET]:
    """Create new filter from the old one."""

    @functools.wraps(filter1.function)
    async def func(event: ET) -> bool:
        return operator_(await filter1.call(event))

    return Filter(function=func, event_builder=filter1.event_builder,)


def ensure_filters(
    event_builder: Optional[Type[EventBuilder]],
    filters: Tuple[Union[Filter[ET], Callable[[ET], bool]], ...],
) -> Generator[Filter[ET], None, None]:
    """
    Generator function propagates event builder to event-builder-naive filters
    """
    for filter_ in filters:
        if isinstance(filter_, Filter):
            if not filter_.event_builder:
                filter_.event_builder = event_builder
            yield filter_
        else:
            yield Filter(function=filter_, event_builder=event_builder)
