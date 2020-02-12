import inspect
from typing import Callable, Union

from ..filters.base import Filter

CALLBACK_STATE_KEY = "context"
CURRENT_CLIENT_KEY = "current_client"


class Callback:
    __call__ = None

    def __init__(
        self,
        callback: Union[Callable, "Callback"] = None,
        *filters: Union[Callable, Filter]
    ):
        self.filters = filters
        self.requires_context = False
        self.requires_client = False
        self.key_maker = None
        self.continue_prop = False
        self.empty_arg_handler = False

        if isinstance(callback, Callable):
            self.__call__ = callback

        elif isinstance(callback, Callback):
            callback = callback.__call__

        if not isinstance(self.__call__, Callable):
            # .__call__ must be set by inherited class, otherwise Error
            raise ValueError("Callback must be callable")

        args = inspect.getfullargspec(callback)
        args_cp = args.args.copy()
        args_cp.extend(args.kwonlyargs)

        if not args_cp:
            self.empty_arg_handler = True

        else:
            if CALLBACK_STATE_KEY in args_cp:
                self.requires_context = True

            if CURRENT_CLIENT_KEY in args_cp:
                self.requires_client = True
