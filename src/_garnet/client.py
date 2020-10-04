import asyncio
from typing import Awaitable, Callable

from telethon import errors
from telethon.client.telegramclient import (
    TelegramClient as _TelethonTelegramClient,
)
from telethon.client.updates import EventBuilderDict

from _garnet.helpers import ctx


class TelegramClient(_TelethonTelegramClient, ctx.ContextInstanceMixin):
    __is_telegram_garnet__ = True
    __dispatch_hook__: "Callable[[EventBuilderDict], Awaitable[None]]"

    async def _dispatch_update(self, update, others, channel_id, pts_date):
        if not self._entity_cache.ensure_cached(update):
            if self._state_cache.update(update, check_only=True):
                try:
                    await self._get_difference(update, channel_id, pts_date)
                except OSError:
                    pass  # We were disconnected, that's okay
                except errors.RPCError:
                    pass

        if not self._self_input_peer:
            await self.get_me(input_peer=True)

        built = EventBuilderDict(self, update, others)
        asyncio.create_task(self.__dispatch_hook__(built))


__all__ = ("TelegramClient",)
