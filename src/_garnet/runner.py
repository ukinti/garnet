from typing import Callable, Optional, TypedDict

from _garnet.client import GarnetConfig, TelegramClient
from _garnet.events.dispatcher import EventDispatcher


class RuntimeConfig(TypedDict):
    # todo: more config params
    bot_token: Optional[str]


def default_conf_maker() -> RuntimeConfig:
    from os import getenv

    return RuntimeConfig(
        bot_token=getenv("GARNET_BOT_TOKEN", getenv("BOT_TOKEN")),
    )


class Runner:
    __slots__ = "_bot", "_dispatcher", "_runtime_cfg"

    def __init__(
        self,
        dispatcher: EventDispatcher,
        bot: TelegramClient,
        conf_maker: Callable[[], RuntimeConfig] = default_conf_maker,
        dont_wait_for_handler: bool = False,
    ):
        """
        :param dispatcher: event dispatcher with routers bind to it.
        :param bot: garnet.TelegramClient instance
        :param conf_maker: function that takes nothing and returns RuntimeConfig
        :param dont_wait_for_handler: aggressive event processing mode, that
        only schedules future and does not wait for it
        """

        bot.__garnet_config__ = GarnetConfig(
            dont_wait_for_handler=dont_wait_for_handler,
            dispatch_hook=dispatcher.handle,
        )

        self._bot = bot
        self._dispatcher = dispatcher
        self._runtime_cfg = conf_maker()

    async def run_blocking(self):
        bot_ctx_token = None

        try:
            await self._dispatcher.storage.init()
            self._bot.set_current(self._bot)
            await self._bot.start(bot_token=self._runtime_cfg["bot_token"],)
            await self._bot.run_until_disconnected()
        finally:
            if bot_ctx_token is not None:
                self._bot.reset_current(bot_ctx_token)
            await self._dispatcher.storage.save()
            await self._dispatcher.storage.close()


__all__ = (
    "Runner",
    "RuntimeConfig",
)
