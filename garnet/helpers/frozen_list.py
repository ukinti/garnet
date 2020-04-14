from typing import List, TypeVar, Generic, Optional

T = TypeVar("T")


class PseudoFrozenList(Generic[T]):
    # we don't need  python list's all methods, so don't inherit from it
    def __init__(self):
        self.__items: List[T] = list()
        self.__frozen = False

    @property
    def frozen(self):
        return self.__frozen

    def append(self, *items: T) -> None:
        ap = self.__items.append
        for val in items:
            ap(val)

    def remove(self, *items: T) -> None:
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
        def wrp(item: T):
            self.append(item)

        return wrp
