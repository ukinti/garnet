import functools
from os import getenv
from typing import Any, Callable, Optional, TypedDict

from _garnet.client import GarnetConfig, TelegramClient
from _garnet.events.router import Router
from _garnet.storages.base import BaseStorage


class RuntimeConfig(TypedDict):
    # todo add more config vars
    session_dsn: str
    app_id: str
    app_hash: str
    bot_token: str


def strict_getenv(key: str, /) -> str:
    if (val := getenv(key)) is None:
        raise ValueError(f"No env. var. found for {key}. Please export it.")

    return val


def default_conf_maker() -> RuntimeConfig:
    return RuntimeConfig(
        bot_token=strict_getenv("BOT_TOKEN"),
        app_id=strict_getenv("APP_ID",),
        app_hash=strict_getenv("APP_HASH"),
        session_dsn=strict_getenv("SESSION_DSN"),
    )


async def run(
    router: Router,
    storage: BaseStorage[Any],
    bot: Optional[TelegramClient] = None,
    conf_maker: Callable[[], RuntimeConfig] = default_conf_maker,
    dont_wait_for_handler: bool = False,
) -> None:
    if bot is None:
        runtime_cfg = conf_maker()

        if not isinstance(runtime_cfg["session_dsn"], str):
            raise ValueError  # todo

        bot = TelegramClient(
            session=runtime_cfg["session_dsn"],
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
        if not bot.is_connected():
            runtime_cfg = conf_maker()
            await bot.start(bot_token=runtime_cfg["bot_token"],)
        await bot.run_until_disconnected()
    finally:
        if bot_ctx_token is not None:
            bot.reset_current(bot_ctx_token)
        await storage.close()


__all__ = (
    "run",
    "RuntimeConfig",
)
