# PseudoFrozenList can be frozen at the some point of time
from typing import List, Iterable, Any
import itertools


class PseudoFrozenList:
    # we don't need  python list's all methods, so don't inherit from it
    @staticmethod  # noqa
    def __class_getitem__(*types_):
        return PseudoFrozenList(*types_)

    def __init__(self, *types_: Any):
        for t in types_:
            if not isinstance(t.__class__, type):
                raise ValueError(f"Expected class, got {t!r}")

        self.__types = tuple(itertools.chain(types_))
        self.__items: List[Any] = list()
        self.__frozen = False

    @property
    def frozen(self):
        return self.__frozen

    def __validation(self, val):
        if self.__frozen:
            raise RuntimeWarning(
                f"{val!r} cannot be appended/removed, list is already frozen."
            )

        if not isinstance(val, self.__types):
            raise ValueError(
                f"Only {self.__types!r} can be appended/removed, got {val!r}"
            )

    def append(self, *items: Any) -> None:
        self.__validation(*items)
        ap = self.__items.append
        for val in items:
            ap(val)

    def remove(self, *items: Any) -> None:
        self.__validation(*items)
        rm = self.__items.remove
        for val in items:
            rm(val)

    def freeze(self):
        self.__frozen = True

    def __iter__(self):
        return list.__iter__(self.__items)

    # decorator for append
    @property
    def __call__(self):
        def wrp(item: Any):
            self.append(item)

        return wrp
