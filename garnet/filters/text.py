import operator
import typing
import re

from .base import Filter


def _base_len_comparator(operator_, predicted_length):
    if predicted_length is None:
        return Filter(lambda update: operator_(len(update.raw_text or "")))
    else:
        return Filter(
            lambda update: operator_(len(update.raw_text or ""), predicted_length)
        )


def startswith(prefix: str) -> Filter:
    """
    Check if .event.raw_text startswith prefix
    :return:
    """
    return Filter(
        lambda update: update.raw_text.startswith(prefix)
        if isinstance(update.raw_text, str)
        else None
    )


def commands(
    *cmd: str, prefixes: typing.Union[str, typing.Iterable[str]] = "/"
) -> Filter:
    return Filter(
        lambda update: isinstance(update.text, str)
        and any(update.text.startswith(prefix) for prefix in prefixes)
        and update.text.split()[0][1:] in cmd
    )


def match(expression: str) -> Filter:
    return Filter(lambda update: re.compile(expression).match(update.raw_text))


def exact(text: str) -> Filter:
    return Filter(lambda update: update.raw_text == text)


def between(*texts: str) -> Filter:
    return Filter(lambda update: update.raw_text in texts)


def isdigit() -> Filter:
    return Filter(lambda update: (update.raw_text or "").isdigit())


class MessageLenMeta(type):
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


class Len(metaclass=MessageLenMeta):
    """
    Text Length
    """
