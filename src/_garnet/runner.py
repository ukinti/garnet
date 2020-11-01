import functools
from typing import Callable, NoReturn, Optional, TypedDict

from _garnet.client import GarnetConfig, TelegramClient
from _garnet.events.router import Router
from _garnet.storages.base import BaseStorage


class RuntimeConfig(TypedDict):
    # todo add more config vars
    session: Optional[str]
    app_id: Optional[str]
    app_hash: Optional[str]
    bot_token: Optional[str]


def default_conf_maker() -> RuntimeConfig:
    from os import getenv

    return RuntimeConfig(
        bot_token=getenv("GARNET_BOT_TOKEN", getenv("BOT_TOKEN")),
        app_id=getenv("APP_ID", getenv("API_ID")),
        app_hash=getenv("APP_HASH", getenv("API_HASH")),
        session=getenv("SESSION", "~garnet-default.session"),
    )


async def run(
    router: Router,
    storage: BaseStorage,
    bot: Optional[TelegramClient] = None,
    conf_maker: Callable[[], RuntimeConfig] = default_conf_maker,
    dont_wait_for_handler: bool = False,
) -> NoReturn:
    runtime_cfg = conf_maker()

    if bot is None:
        bot = TelegramClient(
            session=runtime_cfg["session"],
            api_id=int(runtime_cfg["app_id"]),
            api_hash=runtime_cfg["app_hash"],
        )

    bot.__garnet_config__ = GarnetConfig(
        dont_wait_for_handler=dont_wait_for_handler,
        dispatch_hook=functools.partial(router.notify, storage),
    )

    bot_ctx_token = None

    try:
        await storage.init()
        bot.set_current(bot)
        await bot.start(bot_token=runtime_cfg["bot_token"],)
        await bot.run_until_disconnected()
    finally:
        if bot_ctx_token is not None:
            bot.reset_current(bot_ctx_token)
        await storage.save()
        await storage.close()


__all__ = (
    "run",
    "RuntimeConfig",
)
