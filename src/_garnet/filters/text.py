import functools
import operator
import re
from typing import Any, Callable, Iterable, Type, Union

from _garnet.events.filter import Filter
from _garnet.patched_events import NewMessage


def _base_len_comparator(
    operator_: Union[Callable[[int, int], bool], Callable[[int], bool]],
    predicted_length: int,
) -> Filter[NewMessage.Event]:
    if predicted_length is None:
        return Filter(
            lambda update: operator_(len(update.raw_text or "")),
            event_builder=NewMessage,
        )
    else:
        return Filter(
            lambda update: operator_(
                len(update.raw_text or ""), predicted_length
            ),
            event_builder=NewMessage,
        )


def _return_false_on_error(
    no_param_func: Callable[[], Any], exception: Type[BaseException], /,
) -> bool:
    try:
        no_param_func()
        return True
    except exception:
        return False


def startswith(prefix: str, /) -> Filter:
    """
    Check if Some.raw_text::str starts with prefix
    """
    return Filter(
        lambda update: update.raw_text.startswith(prefix)
        if isinstance(update.raw_text, str)
        else None,
        event_builder=NewMessage,
    )


def commands(
    *cmd: str, prefixes: Union[str, Iterable[str]] = "/", to_set: bool = True,
) -> Filter:
    """
    Check if cmd Some.text::str is a command.
    Uses Set.__contains__ if to_set is True (which is faster)
    """
    if to_set:
        cmd = set(cmd)

    return Filter(
        lambda update: isinstance(update.text, str)
        and any(update.text.startswith(prefix) for prefix in prefixes)
        and (update.text.split(maxsplit=1)[0][1:].split("@", maxsplit=1)[0])
        in cmd,
        event_builder=NewMessage,
    )


def match(expression: str, flags: int = 0, /) -> Filter[NewMessage.Event]:
    """
    Check if Some.raw_text::str does match a pattern.
    """
    rex = re.compile(expression, flags=flags)

    return Filter(
        lambda update: bool(rex.match(update.raw_text)),
        event_builder=NewMessage,
    )


def exact(text: str, /) -> Filter[NewMessage.Event]:
    """
    Check if Some.raw_text::str is equal to text.
    """
    return Filter(
        lambda update: update.raw_text == text, event_builder=NewMessage,
    )


def exact_map(
    exact_as: str,
    f: Callable[[str], str],
    /
) -> Filter[NewMessage.Event]:
    """
    Check if f(Some.raw_text::str) is equal f(exact_as)
    """
    # do not pre-compute and cache f(exact_as) since `f` can be designed to
    # work dynamically and mutate its state.
    return Filter(
        lambda update: f(update.raw_text) == f(exact_as),
        event_builder=NewMessage,
    )


def between(*texts: str, to_set: bool = True) -> Filter:
    """
    Check if Some.raw_text::str is equal to text
    Uses Set.__contains__ if to_set is True (which is faster)
    """
    if to_set:
        texts = set(texts)

    return Filter(
        lambda update: update.raw_text in texts, event_builder=NewMessage,
    )


def can_be_int(base: int = 10) -> Filter:
    """
    Check if int(Some.raw_text::str()) does not throw ValueError
    """
    func = functools.partial(int, base=base)

    return Filter(
        lambda event: _return_false_on_error(
            functools.partial(func, event.raw_text), ValueError,
        ),
        event_builder=NewMessage,
    )


def can_be_float() -> Filter:
    """
    Check if float(Some.raw_text::str()) does not throw ValueError
    """
    return Filter(
        lambda event: _return_false_on_error(
            functools.partial(float, event.raw_text), ValueError,
        ),
        event_builder=NewMessage,
    )


class _MessageLenMeta(type):
    def __eq__(self, length: int) -> Filter[NewMessage.Event]:
        return _base_len_comparator(operator.eq, length)

    def __gt__(self, length: int) -> Filter[NewMessage.Event]:
        return _base_len_comparator(operator.gt, length)

    def __lt__(self, length: int) -> Filter[NewMessage.Event]:
        return _base_len_comparator(operator.lt, length)

    def __ge__(self, length: int) -> Filter[NewMessage.Event]:
        return _base_len_comparator(operator.ge, length)

    def __le__(self, length: int) -> Filter[NewMessage.Event]:
        return _base_len_comparator(operator.le, length)


class Len(metaclass=_MessageLenMeta):
    """
    Basic tests for Some.raw_text::str length

    Example:

    >>> from garnet.filters import text
    >>> text.Len == 1  # will produce `Filter` object
    ...
    >>> (text.Len >= 24) & (text.Len <= 42)  # will produce new `Filter` too
    ...
    >>>
    """
