from typing import Container, Union

from _garnet.events.filter import Filter
from _garnet.vars import fsm

ANY_STATE_EXCEPT_NONE = "*"


async def any_state_except_none_func(_):
    return await fsm.StateCtx.get().get_state() is not None


_ilc_descriptor = type(
    "InstanceLessProperty",
    (),
    {
        "__slots__": ("value",),
        "__get__": lambda dptor, instance, owner: dptor.value,
        "__init__": lambda dptor, value: setattr(dptor, "value", value),
    },
)


class _MetaCurrentState(type):
    @classmethod
    def __eq__(mcs, _s: Union[str, Container[str]]) -> Filter:
        if _s == ANY_STATE_EXCEPT_NONE:

            async def _f(_):
                return await fsm.StateCtx.get().get_state() is not None

        elif not isinstance(_s, str) and isinstance(_s, Container):

            async def _f(_):
                return (await fsm.StateCtx.get().get_state()) in _s

        else:

            async def _f(_):
                return (await fsm.StateCtx.get().get_state()) == _s

        return Filter(_f, None)

    @classmethod
    def exact(mcs, state: Union[str, Container[str]]) -> Filter:
        # noinspection PyTypeChecker
        return State == state  # type: ignore

    any: Filter = _ilc_descriptor(
        Filter(any_state_except_none_func, event_builder=None)
    )


class State(metaclass=_MetaCurrentState):
    """
    Class with implemented in metaclass magic methods.
    Any state: ANY_STATE states "*". Simply use equality operator to builtin methods
        CurrentState == "*"
    Particular state(s):
        CurrentState == ["state_1", "state_2"]
        CurrentState == "state_1"
    """


__all__ = ("State",)
