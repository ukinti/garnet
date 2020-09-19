import asyncio as _asyncio
import contextvars
import functools


async def to_thread(func, /, ctx: contextvars.Context):
    loop = _asyncio.events.get_running_loop()
    func_call = functools.partial(ctx.run, func)
    return await loop.run_in_executor(None, func_call)
