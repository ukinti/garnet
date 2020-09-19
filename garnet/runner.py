from garnet import TelegramClient
from garnet.events.dispatcher import EventDispatcher


class Runner:
    __slots__ = "_bot", "_dispatcher", "_trust_env"

    def __init__(
        self, dispatcher: EventDispatcher, bot: TelegramClient, trust_env: bool,
    ):
        # funny how `all` comes handy in here
        setattr(bot, "__dispatch_hook__", dispatcher.handle),

        self._bot = bot
        self._dispatcher = dispatcher
        self._trust_env = trust_env

    async def run_blocking(self):
        try:
            self._bot.set_current(self._bot)
            await self._bot.start()
            await self._bot.run_until_disconnected()
        finally:
            pass
