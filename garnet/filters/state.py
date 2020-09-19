from typing import Container, Union

from garnet.events.filter import Filter
from garnet.vars.fsm import State

ANY_STATE = (id(all), id(any))


class _MetaCurrentState(type):
    @classmethod
    def __eq__(mcs, _s: Union[str, Container[str]]) -> Filter:
        if id(_s) in ANY_STATE:

            def _f(_):
                return True

        elif not isinstance(_s, str) and isinstance(_s, Container):

            async def _f(_):
                return (await State.get().get_state()) in _s

        else:

            async def _f(_):
                return (await State.get().get_state()) == _s

        return Filter(_f)

    @classmethod
    def exact(mcs, state: Union[str, Container[str]]) -> Filter:
        # noinspection PyTypeChecker
        return CurrentState == state  # type: ignore


class CurrentState(metaclass=_MetaCurrentState):
    """
    Class with implemented in metaclass magic methods.
    Any state: ANY_STATE states "*". Simply use equality operator to builtin methods
        CurrentState == all
        CurrentState == any
    Particular state(s):
        CurrentState == ["state_1", "state_2"]
        CurrentState == "state_1"
    """


__all__ = ("CurrentState",)
