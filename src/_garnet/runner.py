from _garnet.client import TelegramClient, GarnetConfig
from _garnet.events.dispatcher import EventDispatcher


class Runner:
    __slots__ = "_bot", "_dispatcher", "_trust_env"

    def __init__(
        self,
        dispatcher: EventDispatcher,
        bot: TelegramClient,
        trust_env: bool,
        dont_wait_for_handler: bool = False,
    ):
        bot.__garnet_config__ = GarnetConfig(
            dont_wait_for_handler=dont_wait_for_handler,
            dispatch_hook=dispatcher.handle,
        )

        self._bot = bot
        self._dispatcher = dispatcher
        self._trust_env = trust_env

    async def run_blocking(self):
        bot_ctx_token = None

        try:
            await self._dispatcher.storage.init()
            self._bot.set_current(self._bot)
            await self._bot.start()
            await self._bot.run_until_disconnected()
        finally:
            if bot_ctx_token is not None:
                self._bot.reset_current(bot_ctx_token)
            await self._dispatcher.storage.save()
            await self._dispatcher.storage.close()
