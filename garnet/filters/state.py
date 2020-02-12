from typing import List, Callable, Dict, Any, Tuple, Union, Sequence

from telethon.events import common

from .base import Filter
from ..storages.base import FSMContext

ANY_STATE = (id(all), id(any))
KeyMakerType = Callable[[common.EventBuilder], Dict[str, Any]]


class _MetaCurrentState(type):
    @classmethod
    def __matmul__(mcs, key_maker: Tuple[str, KeyMakerType]) -> Filter:
        equal_to_state, key_maker = key_maker

        async def _f(event, context: FSMContext):
            # any context can be passed, just a small hack
            return await context.storage.get_state(**key_maker(event)) == equal_to_state

        f_ = Filter(_f, requires_context=True)
        f_.key_maker = key_maker
        return f_

    @classmethod
    def __rmatmul__(mcs, key_maker: Tuple[str, KeyMakerType]) -> Filter:
        return CurrentState @ key_maker

    @classmethod
    def __eq__(mcs, _s: Union[str, List[str]]) -> Filter:
        if id(_s) in ANY_STATE:

            async def _f(_, context):
                return (await context.get_state()) is not None

        elif isinstance(_s, Sequence):

            async def _f(_, context):
                return (await context.get_state()) in _s

        else:

            async def _f(_, context):
                return (await context.get_state()) == _s

        return Filter(_f, requires_context=True, state_op=True)

    @classmethod
    def exact(mcs, state: Union[str, List[str]]) -> Filter:
        # noinspection PyTypeChecker
        return CurrentState == state  # type: ignore

    @classmethod
    def with_key(mcs, state: str, key_maker: KeyMakerType):
        return CurrentState @ (state, key_maker)


class CurrentState(metaclass=_MetaCurrentState):
    """
    Class with implemented in metaclass magic methods

    CurrentState @ ("state_name", key_maker)
        key_maker is a callable with signature: (event) -> Dict[str, Any]
        For instance:
            >>> def my_key_maker(event) -> Dict[str, Any]:
            ...     return {"chat": event.chat.id, event.user.id}
            ...
            >>> CurrentState @ ("equlas_to_the_state", my_key_maker)
            ... <garnet.filters.base.Filter object at 0x7f8bebe996>
            >>> # same approaching from the right side.
            >>> ("equlas_to_the_state", my_key_maker) @ CurrentState
            ... <garnet.filters.base.Filter object at 0x7f8baba001>

    Any state: ANY_STATE states "*". Simply use equality operator to builtin methods
        CurrentState == all
        CurrentState == any

    Particular state(s):
        CurrentState == ["state_1", "state_2"]
        CurrentState == "state_1"

    """


__all__ = ("CurrentState",)
