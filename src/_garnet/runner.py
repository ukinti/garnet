import asyncio
import functools
import logging
import sys
from os import getenv
from typing import Any, Awaitable, Callable, NoReturn, Optional, TypedDict

from _garnet.client import GarnetConfig, TelegramClient
from _garnet.events.router import Router
from _garnet.loggers import runtime
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
    print_: Optional[Callable[..., None]] = functools.partial(print, sep="\n"),
) -> NoReturn:
    if bot is None:
        runtime_cfg = conf_maker()

        if not isinstance(runtime_cfg["session_dsn"], str):
            raise ValueError  # todo

        bot = TelegramClient(
            session=runtime_cfg["session_dsn"],
            api_id=int(runtime_cfg["app_id"]),
            api_hash=runtime_cfg["app_hash"],
        )

        if callable(print_):
            app_id = runtime_cfg["app_id"]
            app_hash = runtime_cfg["app_hash"]
            app_hash = app_hash[:8] + ("*" * (len(app_hash) - 8))
            bot_token = runtime_cfg["bot_token"]
            bot_token = bot_token[:8] + ("*" * (len(bot_token) - 8))
            session_dsn = runtime_cfg["session_dsn"]
            session_dsn = session_dsn[:4] + ("*" * (len(session_dsn) - 4))

            print_(
                "🔧 Using config(",
                f"    {app_id=},",
                f"    {app_hash=},",
                f"    {bot_token=},",
                f"    {session_dsn=}"
                ")",
            )

    bot.__garnet_config__ = GarnetConfig(
        dont_wait_for_handler=dont_wait_for_handler,
        dispatch_hook=functools.partial(router.notify, storage),
    )

    if callable(print_):
        print_(f"☄️ Propagate events chaotically: {dont_wait_for_handler}",)

    bot_ctx_token = None

    try:
        await storage.init()
        bot_ctx_token = bot.set_current(bot)
        if not bot.is_connected():
            runtime_cfg = conf_maker()
            await bot.start(bot_token=runtime_cfg["bot_token"],)
        await bot.run_until_disconnected()
    finally:
        if bot_ctx_token is not None:
            bot.reset_current(bot_ctx_token)
        await storage.close()


def launch(
    run_coro: Awaitable[NoReturn], app_name: str = "my-awesome-bot", /,
) -> NoReturn:
    configure_logging(app_name)
    loop = asyncio.new_event_loop()
    try:
        runtime.info(f"Starting {app_name}...")
        asyncio.events.set_event_loop(loop)
        return loop.run_until_complete(run_coro)

    except (SystemExit, KeyboardInterrupt, Exception) as e:
        runtime.critical(
            f"Cannot continue. Error: {(e or 'unknown')!r}. Exiting loop..."
        )

    finally:
        try:
            runtime.info("Cancelling asyncio tasks")
            cancellable = asyncio.all_tasks(loop)
            for task in cancellable:
                task.cancel()

            loop.run_until_complete(loop.shutdown_asyncgens())
            loop.run_until_complete(loop.shutdown_default_executor())
        finally:
            asyncio.events.set_event_loop(None)
            loop.close()


def configure_logging(app_name: str):
    logger = logging.getLogger(app_name)
    logger.setLevel(logging.DEBUG if __debug__ else logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(logging.DEBUG)
        handler.setFormatter(
            logging.Formatter(
                "%(levelname)-5s %(asctime)s %(name)s: %(message)s"
            )
        )

        logger.addHandler(handler)
