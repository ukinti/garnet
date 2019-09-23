# PseudoFrozenList can be frozen at the some point of time

from typing import List, Iterable, Any


class PseudoFrozenList:
    # we don't need  python list's all methods, so don't inherit from it
    def __init__(self, type_: Any):
        if not isinstance(type_.__class__, type):
            raise ValueError(f"Expected class, got {type_!r}")

        self.__type = type_
        self.__items: List[type_] = list()
        self.__frozen = False

    @property
    def frozen(self):
        return self.__frozen

    def __validation(self, callback):
        if isinstance(callback, Iterable):
            for callback_ in callback:
                self.__validation(callback_)

        if self.__frozen:
            raise RuntimeWarning(
                f"{callback!r} cannot be appended/removed, list is already frozen."
            )

        if not isinstance(callback, self.__type):
            raise ValueError(
                f"Only {self.__type!r} can be appended/removed, got {callback!r}"
            )

    def append(self, *items: Any) -> None:
        self.__validation(*items)
        ap = self.__items.append
        for callback_ in items:
            ap(callback_)

    def remove(self, *items: Any) -> None:
        self.__validation(*items)
        rm = self.__items.remove
        for callback_ in items:
            rm(callback_)

    def freeze(self):
        self.__frozen = True

    def __iter__(self):
        return list.__iter__(self.__items)

    # decorator for append
    @property
    def __call__(self):
        def wrp(item: Any):
            self.__validation(item)
            self.append(item)

        return wrp
