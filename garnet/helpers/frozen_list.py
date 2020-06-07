import inspect
from functools import update_wrapper
from typing import Any, List, TypeVar, Generic, Iterator, Callable

T = TypeVar("T")


class PseudoFrozenList(Generic[T]):
    # we don't need  python list's all methods, so don't inherit from it
    def __init__(self):
        self.__items: List[T] = []
        self.__frozen = False

    @property
    def frozen(self) -> bool:
        return self.__frozen

    def append(self, *items: T) -> None:
        ap = self.__items.append
        for val in items:
            ap(val)

    def remove(self, *items: T) -> None:
        rm = self.__items.remove
        for val in items:
            rm(val)

    def freeze(self) -> None:
        self.__frozen = True

    def __iter__(self) -> Iterator[T]:
        return iter(self.__items)

    # decorator for append, when T is Callable[..., Any]
    def __call__(self) -> Callable[[T], T]:
        def decorator(func) -> T:
            self.append(func)

            if inspect.iscoroutinefunction(func):
                async def wrp(*args, **kwargs) -> Any:
                    return await func(*args, **kwargs)
            else:
                def wrp(*args, **kwargs) -> Any:
                    return func(*args, **kwargs)

            return update_wrapper(wrp, func)

        return decorator
