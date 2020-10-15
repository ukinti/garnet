import functools
import operator
import re
import typing

from _garnet.events.filter import Filter


def _base_len_comparator(operator_, predicted_length):
    if predicted_length is None:
        return Filter(lambda update: operator_(len(update.raw_text or "")))
    else:
        return Filter(
            lambda update: operator_(
                len(update.raw_text or ""), predicted_length
            )
        )


def _return_false_on_error(no_param_func, exception, /) -> bool:
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
        else None
    )


def commands(
    *cmd: str,
    prefixes: typing.Union[str, typing.Iterable[str]] = "/",
    to_set: bool = True,
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
        and (update.text
             .split(maxsplit=1)[0][1:]
             .split("@", maxsplit=1)[0]) in cmd
    )


def match(expression: str, flags: int = 0, /) -> Filter:
    """
    Check if Some.raw_text::str does match a pattern.
    """
    rex = re.compile(expression, flags=flags)

    return Filter(
        lambda update: bool(rex.match(update.raw_text))
    )


def exact(text: str, /) -> Filter:
    """
    Check if Some.raw_text::str is equal to text.
    """
    return Filter(lambda update: update.raw_text == text)


def between(*texts: str, to_set: bool = True) -> Filter:
    """
    Check if Some.raw_text::str is equal to text
    Uses Set.__contains__ if to_set is True (which is faster)
    """
    if to_set:
        texts = set(texts)

    return Filter(lambda update: update.raw_text in texts)


def can_be_int(base: int = 10) -> Filter:
    """
    Check if int(Some.raw_text::str()) does not throw ValueError
    """
    func = functools.partial(int, base=base)

    return Filter(
        lambda event: _return_false_on_error(
            functools.partial(func, event.raw_text),
            ValueError,
        )
    )


def can_be_float() -> Filter:
    """
    Check if float(Some.raw_text::str()) does not throw ValueError
    """
    return Filter(
        lambda event: _return_false_on_error(
            functools.partial(float, event.raw_text),
            ValueError,
        )
    )


class _MessageLenMeta(type):
    def __eq__(self, length: int) -> Filter:
        return _base_len_comparator(operator.eq, length)

    def __gt__(self, length: int) -> Filter:
        return _base_len_comparator(operator.gt, length)

    def __lt__(self, length: int) -> Filter:
        return _base_len_comparator(operator.lt, length)

    def __ge__(self, length: int) -> Filter:
        return _base_len_comparator(operator.ge, length)

    def __le__(self, length: int) -> Filter:
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
