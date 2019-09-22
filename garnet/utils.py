# PseudoFrozenList can be frozen at the some point of time

from typing import List, cast, Callable, Iterable


class PseudoFrozenList:
    # we don't need  python list's all methods, so don't inherit from it
    def __init__(self):
        self.__callbacks: List[Callable] = list()
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

        if not isinstance(callback, Callable):
            raise ValueError(
                f"Only {Callable!r} can be appended/removed, got {callback!r}"
            )

    def append(self, *callback: Callable) -> None:
        self.__validation(*callback)
        ap = self.__callbacks.append
        for callback_ in callback:
            ap(callback_)

    def remove(self, *callback: Callable) -> None:
        self.__validation(*callback)
        rm = self.__callbacks.remove
        for callback_ in callback:
            rm(callback_)

    def freeze(self):
        self.__frozen = True

    def __iter__(self):
        return list.__iter__(self.__callbacks)


cast(PseudoFrozenList, List[Callable])
