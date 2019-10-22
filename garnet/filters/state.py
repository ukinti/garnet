from typing import List, Callable, Dict, Any

from telethon.events import common

from .base import Filter
from ..storages.base import FSMContext


def ckey(
    equal_to_state: str, key_maker: Callable[[common.EventBuilder], Dict[str, Any]]
):
    async def _f(event, context: FSMContext):
        # any context can be passed, just a small hack
        return await context.storage.get_state(**key_maker(event)) == equal_to_state

    f_ = Filter(_f, requires_context=True)
    f_.key_maker = key_maker
    return f_


custom_key = with_key = from_key = ckey


def exact(state: str) -> Filter:
    async def _f(event, context):
        return (await context.get_state()) == state

    return Filter(_f, requires_context=True, state_op=True)


def between(states: List[str]) -> Filter:
    async def _f(event, context):
        return (await context.get_state()) in states

    return Filter(_f, requires_context=True, state_op=True)


def every() -> Filter:
    """
    In any state
    """
    async def _f(event, context):
        return (await context.get_state()) is not None

    return Filter(_f, requires_context=True, state_op=True)


__all__ = (
    "every",
    "exact",
    "between",
    "ckey",
    "custom_key",
    "with_key",
    "from_key",
)
