import inspect
from typing import Callable


class Filter:
    def __init__(self, function: Callable, requires_context: bool = False):
        if isinstance(function, Filter):
            self.__name__ = function.__name__
            self.function = function.function
            self.awaitable = function.awaitable
            self.requires_context = function.requires_context

        else:
            name = function.__name__
            if name == "<lambda>":
                name = f"{function!s}"

            self.__name__ = f"Garnet:Filter:{name}"

            self.function = function
            self.awaitable = False
            self.requires_context = requires_context

            if inspect.iscoroutinefunction(function) or inspect.isawaitable(function):
                self.awaitable = True

        self.key_maker = False
