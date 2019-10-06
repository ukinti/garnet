import abc

from ..events import common
from ..helpers.frozen_list import PseudoFrozenList
from ..filters import Filter
from ..callbacks.base import Callback


class AbstractRouter(abc.ABC):
    def __init__(self, frozen: bool = False):
        """
        Abstract Router
        :param frozen: While registering router it can be frozen once.
        """
        self.frozen = frozen
        self.handlers = PseudoFrozenList[tuple]

    @abc.abstractmethod
    def register(self, *args, **kwargs):
        raise NotImplementedError()

    __call__ = on = register

    @abc.abstractmethod
    def non_blocking(self, *args, **kwargs):
        """
        Register handlers in non-blocking way.
        Such as event goes through all `non-blocking` handlers one-by-one ignoring !ALL! exceptions:
        telegram -> update -> execute_all([handler1(update), handler2(update)]) -> happiness and uncertainty

        whereas normal behaviour:
        telegram -> update -> execute_till_filter_success([handler1(update), handler2(update)]) -> just happiness
        """
        raise NotImplementedError()


class TelethonRouter(AbstractRouter):
    """
    Telethon's TgClient.__on__(event) signature followed

    A way to achieve compatibility with telethon event registering.

    Telethon lovers router <3
    """

    def __init__(self, frozen: bool = False):
        super().__init__(frozen)

    def register(self, event: common.EventBuilder):
        def decorator(f):
            self.handlers.append((f, event, ()))
            return f

        return decorator

    __call__ = on = register

    def non_blocking(self, event: common.EventBuilder):
        def decorator(f):
            c = Callback(f)
            c.continue_prop = True
            self.handlers.append((c, event, ()))
            return f

        return decorator


class Router(AbstractRouter):
    """
    Garnet's TgClient.on(*filters, event=NewMessage) signature followed
    """
    def __init__(self, frozen: bool = False):
        super().__init__(frozen)

    def register(self, *filters: Filter, event: common.EventBuilder = None):
        def decorator(f):
            self.handlers.append((f, event, filters))
            return f

        return decorator

    __call__ = on = register

    def non_blocking(self, *filters: Filter, event: common.EventBuilder = None):
        def decorator(f):
            c = Callback(f)
            c.continue_prop = True
            self.handlers.append((c, event, filters))
            return f

        return decorator
