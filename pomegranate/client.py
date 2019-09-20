from typing import Union, Callable, Sequence, List, Optional
import asyncio
import inspect
import os

from telethon.client.telegramclient import TelegramClient as _TelegramClient
from telethon.events import (
    StopPropagation,
    NewMessage,
    InlineQuery,
    CallbackQuery,
    ChatAction,
    MessageEdited,
    Album,
    UserUpdate,
    common,
)
from telethon.client.updates import EventBuilderDict
from telethon.sessions import Session

from .filters.base import Filter
from .fsm.storages import base, memory

FILTERS_ARG = "_xelethon__Filters"
CALLBACK_STATE_KEY = "context"
STATE_SENSITIVE = (
    NewMessage,
    InlineQuery,
    CallbackQuery,
    ChatAction,
    MessageEdited,
    Album,
    UserUpdate,
)


class TelegramClient(_TelegramClient):
    storage: base.BaseStorage = None

    class Env:
        default_session_key = "SESSION"
        default_api_id_key = "API_ID"
        default_api_hash_key = "API_HASH"
        default_bot_token_key = "BOT_TOKEN"

    def __init__(
            self,
            session: Union[str, Session],
            api_id: int,
            api_hash: str,
            *args,
            storage: base.BaseStorage = None,
            **kwargs
    ):
        self.storage = storage
        self.__bot_token = None
        super(TelegramClient, self).__init__(session, api_id, api_hash, *args, **kwargs)

    @classmethod
    def from_env(
            cls,
            default_session_name: Union[str, Session] = None,
            default_api_id: Optional[int] = None,
            default_api_hash: Optional[str] = None,
            bot_token: Optional[str] = None,
            storage: base.BaseStorage = memory.MemoryStorage,
            *args, **kwargs
    ):
        obj = cls(
            session=os.getenv(cls.Env.default_session_key, default_session_name),
            api_id=os.getenv(cls.Env.default_api_id_key, default_api_id),
            api_hash=os.getenv(cls.Env.default_api_hash_key, default_api_hash),
            storage=storage,
            *args, **kwargs
        )
        obj.__bot_token = os.getenv(cls.Env.default_bot_token_key, bot_token)
        return obj

    def start_as_bot(self, reset_token: str = None):
        return self.start(bot_token=(reset_token if isinstance(reset_token, str) else self.__bot_token))

    @staticmethod
    def make_fsm_key(update, *, _check=True) -> dict:
        if _check and not isinstance(update, STATE_SENSITIVE):
            raise Warning(f"State won't be checked! {update!r} peers can not be determined.")
        return {"user": update.chat_id, "chat": update.from_id}

    def current_state(self, *, user, chat):
        return base.FSMContext(storage=self.storage, user=user, chat=chat)
    # end-fsm-key-region

    def on(
        self,
        *filters: Union[Callable, Filter],
        event: common.EventBuilder = NewMessage,
    ):
        """
        Decorator used to `add_event_handler` more conveniently.
        """
        def decorator(f):
            self.add_event_handler(f, event, *filters)
            return f

        return decorator

    # noinspection PyTypeChecker
    def message_handler(self, *filters: Union[Callable, Filter]): return self.on(*filters, event=NewMessage)
    # noinspection PyTypeChecker
    def callback_query_handler(self, *filters: Union[Callable, Filter]): return self.on(*filters, event=CallbackQuery)
    # noinspection PyTypeChecker
    def chat_action_handler(self, *filters: Union[Callable, Filter]): return self.on(*filters, event=ChatAction)
    # noinspection PyTypeChecker
    def message_edited_handler(self, *filters: Union[Callable, Filter]): return self.on(*filters, event=MessageEdited)
    # noinspection PyTypeChecker
    def album_handler(self, *filters: Union[Callable, Filter]): return self.on(*filters, event=Album)

    def add_event_handler(
            self,
            callback: Callable,
            event=None,
            *filters: Union[Callable, Filter],
    ):
        if filters is not None and not isinstance(filters, Sequence):
            filters = (filters, )

        if isinstance(filters, Sequence):
            if hasattr(callback, FILTERS_ARG):
                raise RuntimeError(f"Usage of {FILTERS_ARG} in function arguments is deprecated!")

            funcs: List[Filter] = []
            for filter_ in filters:
                if isinstance(getattr(filter_, "stack", None), Sequence):
                    funcs.extend(filter_.stack)
                elif isinstance(filter_, Filter):
                    funcs.append(filter_)
                elif isinstance(filter_, Callable):
                    funcs.append(Filter(filter_))

            setattr(callback, FILTERS_ARG, funcs)

        super().add_event_handler(callback, event)

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
        for builder, callback in self._event_builders:
            event = built[type(builder)]
            if not event:
                continue

            if not builder.resolved:
                await builder.resolve(self)

            if not builder.filter(event):
                continue

            filters: List[Filter] = getattr(callback, FILTERS_ARG, ())
            succeed = True
            key = self.make_fsm_key(event, _check=False)
            context = self.current_state(**key)

            if filters:
                for filter_ in filters:
                    if filter_.requires_context and self.storage:
                        if not await filter_.function(event, context=context):
                            succeed = False
                            break
                    elif not (await filter_.function(event) if filter_.awaitable else filter_.function(event)):
                        succeed = False
                        break

            if not succeed:
                continue

            try:
                args = inspect.getfullargspec(callback)
                _args_cp = args.args.copy()
                _args_cp.extend(args.kwonlyargs)
                pass_args = {}
                if CALLBACK_STATE_KEY in _args_cp:
                    pass_args[CALLBACK_STATE_KEY] = context

                if succeed:
                    return await callback(event, **pass_args)
            except StopPropagation:
                name = getattr(callback, '__name__', repr(callback))
                self._log[__name__].debug(
                    'Event handler "%s" stopped chain of propagation '
                    'for event %s.', name, type(event).__name__
                )
                break
            except Exception as e:
                if not isinstance(e, asyncio.CancelledError) or self.is_connected():
                    name = getattr(callback, '__name__', repr(callback))
                    self._log[__name__].exception('Unhandled exception on %s',
                                                  name)

    def run_until_disconnected(self: 'TelegramClient'):
        if self.loop.is_running():
            return self._run_until_disconnected()
        try:
            return self.loop.run_until_complete(self._run_until_disconnected())
        except KeyboardInterrupt:
            pass
        finally:
            # No loop.run_until_complete; it's already syncified
            self.disconnect()
