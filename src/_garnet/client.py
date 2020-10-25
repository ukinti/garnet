import asyncio
from typing import Awaitable, Callable, TypedDict

from telethon import errors
from telethon.client.telegramclient import (
    TelegramClient as _TelethonTelegramClient,
)
from telethon.client.updates import EventBuilderDict

from _garnet.helpers import ctx
from _garnet.loggers import events


class TelegramClient(_TelethonTelegramClient, ctx.ContextInstanceMixin):
    __garnet_config__: "GarnetConfig"

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

        task = asyncio.create_task(
            self.__garnet_config__["dispatch_hook"](built, self),
            name=f"pts_date={pts_date} update propagating",
        )

        if self.__garnet_config__["dont_wait_for_handler"] is False:
            try:
                await task
            except Exception as unhandled_exception:
                if (
                    not isinstance(unhandled_exception, asyncio.CancelledError)
                    or self.is_connected()
                ):
                    events.exception(
                        f"Got an unhandled error for pts_date={pts_date}"
                    )


class GarnetConfig(TypedDict):
    dont_wait_for_handler: bool
    dispatch_hook: Callable[[EventBuilderDict, TelegramClient], Awaitable[None]]


__all__ = (
    "TelegramClient",
    "GarnetConfig",
)
