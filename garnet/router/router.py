from abc import ABC, abstractmethod
from typing import Union, Callable, NoReturn, Sequence, TYPE_CHECKING

from ..events import CallbackQuery, ChatAction, NewMessage, MessageEdited
from ..helpers.frozen_list import PseudoFrozenList
from ..filters import Filter
from ..callbacks.base import Callback

if TYPE_CHECKING:
    from telethon.events import common


class AbstractRouter(ABC):
    frozen: bool
    handlers: Sequence

    @abstractmethod
    def __call__(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def on(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def register(self, *args, **kwargs):
        raise NotImplementedError

    @abstractmethod
    def non_blocking(self, *args, **kwargs):
        """
        Register handlers in non-blocking way.
        Such as event goes through all `non-blocking` handlers one-by-one ignoring !ALL! exceptions:
        telegram -> update -> execute_all([handler1(update), handler2(update)]) -> happiness and uncertainty

        whereas normal behaviour:
        telegram -> update -> execute_till_filter_success([handler1(update), handler2(update)]) -> just happiness
        """
        raise NotImplementedError()


class BaseRouter(AbstractRouter, ABC):
    def __init__(
        self, event: "common.EventBuilder", frozen: bool = False, *filters: Filter
    ):
        """
        BaseRouter
        :param frozen: While registering router it can be frozen once.
        """
        self.event = event
        self.frozen = frozen
        self.handlers: PseudoFrozenList[tuple] = PseudoFrozenList[tuple]
        self.filters = filters

    # noinspection PyTypeChecker
    def message_handler(self, *filters: Union[Callable, Filter]):
        return self.register(*(*filters, *self.filters), event=NewMessage)

    # noinspection PyTypeChecker
    def callback_query_handler(self, *filters: Union[Callable, Filter]):
        return self.register(*(*filters, *self.filters), event=CallbackQuery)

    # noinspection PyTypeChecker
    def chat_action_handler(self, *filters: Union[Callable, Filter]):
        return self.register(*(*filters, *self.filters), event=ChatAction)

    # noinspection PyTypeChecker
    def message_edited_handler(self, *filters: Union[Callable, Filter]):
        return self.register(*(*filters, *self.filters), event=MessageEdited)

    def add_router(self, router: "BaseRouter") -> NoReturn:
        if type(self) != type(router):
            raise ValueError(f"Can bind {router!r} into {self!r}")
        for handler in router.handlers:
            self.handlers.append(handler)
        return self, router


class TelethonRouter(BaseRouter):
    """
    Telethon's TgClient.__on__(event) signature followed

    A way to achieve compatibility with telethon event registering.

    Telethon lovers router <3
    """

    def __init__(self, frozen: bool = False):
        super().__init__(None, frozen)

    def register(self, event: "common.EventBuilder"):
        def decorator(f):
            self.handlers.append((f, event, ()))
            return f

        return decorator

    __call__ = on = register

    def non_blocking(self, event: "common.EventBuilder"):
        def decorator(f):
            c = Callback(f)
            c.continue_prop = True
            self.handlers.append((c, event, ()))
            return f

        return decorator


class Router(BaseRouter):
    """
    Garnet's TelegramClient.on(*filters, event=NewMessage) signature followed
    """

    def __init__(
        self, event: "common.EventBuilder" = None, frozen: bool = False, *filters
    ):
        super().__init__(event, frozen, *filters)

    def register(self, *filters: Filter, event: "common.EventBuilder" = None):
        def decorator(f):
            self.handlers.append((f, event or self.event, (*filters, *self.filters)))
            return f

        return decorator

    def __call__(self, *filters: Filter, event: "common.EventBuilder" = None):
        return self.register(*filters, event=event)

    on = __call__

    def non_blocking(self, *filters: Filter, event: "common.EventBuilder" = None):
        def decorator(f):
            c = Callback(f)
            c.continue_prop = True
            self.handlers.append((c, event or self.event, (*filters, *self.filters)))
            return f

        return decorator
