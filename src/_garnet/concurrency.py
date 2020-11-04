import asyncio
import contextvars
import functools
from typing import Callable, TypeVar, cast

T = TypeVar("T")


async def to_thread(func: Callable[[], T], /) -> T:
    loop = asyncio.events.get_running_loop()
    ctx = contextvars.copy_context()
    func_call = cast(Callable[[], T], functools.partial(ctx.run, func))
    return await loop.run_in_executor(None, func_call)


__all__ = ("to_thread",)
