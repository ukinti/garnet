from typing import Callable, Optional, TypedDict, NoReturn, Tuple

from _garnet.storages.base import BaseStorage
from _garnet.client import GarnetConfig, TelegramClient


class RuntimeConfig(TypedDict):
    # todo: more config params
    bot_token: Optional[str]


def default_conf_maker() -> RuntimeConfig:
    from os import getenv

    return RuntimeConfig(
        bot_token=getenv("GARNET_BOT_TOKEN", getenv("BOT_TOKEN")),
    )


async def run_bot(
    handle_config: Tuple[BaseStorage, Callable],
    bot: TelegramClient,
    conf_maker: Callable[[], RuntimeConfig] = default_conf_maker,
    dont_wait_for_handler: bool = False,
) -> NoReturn:

    runtime_cfg = conf_maker()
    storage, handle_func = handle_config

    bot.__garnet_config__ = GarnetConfig(
        dont_wait_for_handler=dont_wait_for_handler,
        dispatch_hook=handle_func,
    )

    bot_ctx_token = None

    try:
        await storage.init()
        bot.set_current(bot)
        await bot.start(bot_token=runtime_cfg["bot_token"], )
        await bot.run_until_disconnected()
    finally:
        if bot_ctx_token is not None:
            bot.reset_current(bot_ctx_token)
        await storage.save()
        await storage.close()


__all__ = (
    "run_bot",
    "RuntimeConfig",
)
