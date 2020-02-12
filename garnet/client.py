from __future__ import annotations
from typing import (
    Union,
    Callable,
    Sequence,
    List,
    Optional,
    NoReturn,
    Any,
    TYPE_CHECKING,
)
import asyncio
import os
import getpass

from telethon.client.telegramclient import TelegramClient as _TelethonTelegramClient

from garnet.events import StopPropagation, NewMessage, Raw

from .events import EventBuilderDict
from .filters import state
from .filters.base import Filter
from .storages import base, file, memory
from .callbacks.base import (
    Callback,
    CURRENT_CLIENT_KEY,
    CALLBACK_STATE_KEY,
)
from .helpers.frozen_list import PseudoFrozenList
from .router import router
from .helpers import ctx

if TYPE_CHECKING:
    from telethon.events import common


class TelegramClient(_TelethonTelegramClient, ctx.ContextInstanceMixin):
    storage: base.BaseStorage = None

    class Env:
        default_session_dsn_key = "SESSION"
        default_api_id_key = "API_ID"
        default_api_hash_key = "API_HASH"
        default_bot_token_key = "BOT_TOKEN"

    def __init__(
        self,
        session: Any,
        api_id: int,
        api_hash: str,
        *args,
        storage: base.BaseStorage = None,
        **kwargs,
    ):
        if storage is not None and isinstance(storage, type):
            raise ValueError("Got wrong value for storage, initialize your storage")

        super().__init__(session, api_id, api_hash, *args, **kwargs)

        self.storage = storage
        self.__bot_token = None

        self.on_start, self.on_finish, self.on_background = (
            PseudoFrozenList[Callable],
            PseudoFrozenList[Callable],
            PseudoFrozenList[Callable],
        )
        self.set_current(self)

    @classmethod
    def from_env(
        cls,
        default_session_dsn: Optional[str] = None,
        default_api_id: Optional[int] = None,
        default_api_hash: Optional[str] = None,
        bot_token: Optional[str] = None,
        storage: base.BaseStorage = None,
        **kwargs,
    ) -> TelegramClient:
        if any(
            kwarg in kwargs for kwarg in ("session", "api_id", "api_hash", "storage")
        ):
            raise ValueError(
                "Don't pass api_id, api_hash, api_hash to .from_env or pass in default_*"
            )
        obj = cls(
            session=os.getenv(cls.Env.default_session_dsn_key, default_session_dsn),
            api_id=os.getenv(cls.Env.default_api_id_key, default_api_id),
            api_hash=os.getenv(cls.Env.default_api_hash_key, default_api_hash),
            storage=storage,
            **kwargs,
        )

        obj.__bot_token = os.getenv(cls.Env.default_bot_token_key, bot_token)
        obj.set_current(obj)

        if isinstance(storage, (file.JSONStorage,)):

            async def close_storage(*_):
                await storage.close()

            obj.on_finish.append(close_storage)

        return obj

    async def start(
        self: "TelegramClient",
        phone: Callable[[], str] = lambda: input(
            "Please enter your phone (or bot token): "
        ),
        password: Callable[[], str] = lambda: getpass.getpass(
            "Please enter your password: "
        ),
        *,
        bot_token: str = None,
        force_sms: bool = False,
        code_callback: Callable[[], Union[str, int]] = None,
        first_name: str = "New User",
        last_name: str = "",
        max_attempts: int = 3,
    ) -> TelegramClient:
        return await _TelethonTelegramClient.start(**locals())

    async def start_as_bot(self, token: str = None) -> TelegramClient:
        self.set_current(self)
        return await self.start(
            bot_token=(token if isinstance(token, str) else self.__bot_token)
        )

    @classmethod
    def make_fsm_key(cls, update, *, _check=True) -> dict:
        try:
            return {"chat": update.chat_id, "user": update.from_id}
        except AttributeError:
            raise Warning(
                f"Standard make_fsm_key method was not designed for {update!r}"
            )

    def current_state(self, *, user, chat):
        return base.FSMContext(storage=self.storage, user=user, chat=chat)

    # end-fsm-key-region

    def bind_routers(self, *routers: router.AbstractRouter) -> NoReturn:
        for router_ in routers:
            if router_.frozen:
                router_.handlers.freeze()

            for handler, event, filters in router_.handlers:
                self.add_event_handler(handler, event or router_.event, *filters)

    def on(
        self, *filters: Union[Callable, Filter], event: common.EventBuilder = NewMessage
    ):
        """
        Decorator used to `add_event_handler` more conveniently.
        """

        def decorator(f):
            self.add_event_handler(f, event, *filters)
            return f

        return decorator

    def add_event_handler(
        self,
        callback: Union[Callable, Callback],
        event=None,
        *filters: Union[Callable, Filter],
    ):
        if filters is not None and not isinstance(filters, Sequence):
            filters = (filters,)

        _has_state_checker = False
        for filter_ in filters:
            if not isinstance(filter_, (Filter, Callable)):
                raise ValueError(
                    f"Got {type(filter_).__qualname__}, expected Filter or Callable"
                )

            if isinstance(filter_, Filter) and filter_.state_op:
                _has_state_checker = True

        if _has_state_checker is False and self.storage is not None:
            filters = list(filters)
            filters.append(~(state == all))
            filters = tuple(filters)

        elif _has_state_checker and self.storage is None:
            self._log[__name__].warning(
                "No storage was set, but state checker was found, using MemoryStorage for now"
            )
            self.storage = memory.MemoryStorage()

        if not isinstance(callback, Callback):
            callback = Callback(callback, *filters)

        if isinstance(event, type):
            event = event()
        elif not event:
            event = Raw()

        self._event_builders.append((event, callback))

    async def _dispatch_update(self, update, others, channel_id, pts_date):
        if not self._entity_cache.ensure_cached(update):
            # We could add a lock to not fetch the same pts twice if we are
            # already fetching it. However this does not happen in practice,
            # which makes sense, because different updates have different pts.
            if self._state_cache.update(update, check_only=True):
                # If the update doesn't have pts, fetching won't do anything.
                # For example, UpdateUserStatus or UpdateChatUserTyping.
                try:
                    await self._get_difference(update, channel_id, pts_date)
                except OSError:
                    pass
                    # We were disconnected, that's okay

        if not self._self_input_peer:
            # Some updates require our own ID, so we must make sure
            # that the event builder has offline access to it. Calling
            # `get_me()` will cache it under `self._self_input_peer`.
            await self.get_me(input_peer=True)

        built = EventBuilderDict(self, update, others)
        filters_cache = {}
        for builder, callback in self._event_builders:
            event = built[type(builder)]
            if not event:
                continue

            if not builder.resolved:
                await builder.resolve(self)

            if not builder.filter(event):
                continue

            filters: List[Filter] = callback.filters
            succeed = True
            context = None

            if self.storage is not None:
                key_maker_from_filters = (
                    list(
                        filter(
                            lambda f_: hasattr(f_, "key_maker")
                            & (f_.key_maker is not None),
                            filters,
                        )
                    )
                    if filters
                    else None
                )

                key_maker = self.make_fsm_key
                if key_maker_from_filters and isinstance(
                    key_maker_from_filters[0].key_maker, Callable
                ):
                    key_maker = key_maker_from_filters[0].key_maker
                context = base.FSMContext(self.storage, **key_maker(event))

            if filters:
                for filter_ in filters:
                    if filter_ in filters_cache:
                        succeed = filters_cache[filter_]

                    if context is not None and filter_.requires_context:
                        if (await filter_.function(event, context)) is False:
                            succeed = False
                            break

                    else:
                        if (
                            (await filter_.function(event))
                            if filter_.awaitable
                            else filter_.function(event)
                        ) is False:
                            succeed = False
                            break

                    filters_cache[filter_] = succeed

            if succeed is False:
                continue

            try:
                kwargs = {}
                if not callback.empty_arg_handler:
                    if callback.requires_client:
                        kwargs[CURRENT_CLIENT_KEY] = self
                    if callback.requires_context:
                        kwargs[CALLBACK_STATE_KEY] = context

                    coro = callback.__call__(event, **kwargs)
                else:
                    coro = callback.__call__(**kwargs)

                if not callback.continue_prop:
                    return await coro
                try:
                    await coro
                except (Exception, ):
                    continue

            except StopPropagation:
                name = getattr(callback, "__name__", repr(callback))
                self._log[__name__].debug(
                    'Event handler "%s" stopped chain of propagation ' "for event %s.",
                    name,
                    type(event).__name__,
                )
                break
            except Exception as e:
                if not isinstance(e, asyncio.CancelledError) or self.is_connected():
                    name = getattr(callback, "__name__", repr(callback))
                    self._log[__name__].exception("Unhandled exception on %s", name)

    def run_tasks(self, *, finishing: bool):
        self.on_start.freeze()
        self.on_background.freeze()
        self.on_finish.freeze()

        async def bulk_await(wait, background):
            # // ordered awaits
            for callback in wait:
                await callback(self)

            for callback in background:
                self.loop.create_task(callback(self))

        if finishing:
            self.loop.run_until_complete(bulk_await(self.on_finish, ()))
        else:
            self.loop.run_until_complete(bulk_await(self.on_start, self.on_background))

    def run_until_disconnected(self):
        self.run_tasks(finishing=False)

        if self.loop.is_running():
            return self._run_until_disconnected()
        try:
            return self.loop.run_until_complete(self._run_until_disconnected())
        except (KeyboardInterrupt, SystemError, SystemExit):
            pass
        finally:
            self.run_tasks(finishing=True)
            self.disconnect()
            self.loop.stop()


__all__ = ("TelegramClient",)
