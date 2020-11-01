from typing import (
    Container,
    Union,
    Type,
    Any,
    Tuple,
    Dict,
    cast,
    Literal,
)

from _garnet.events.filter import Filter
from _garnet.vars import fsm

ENTRYPOINT_STATE = None
ANY_STATE_EXCEPT_NONE = "*"


NoNext = type("NoNext", (Exception, ), {})
NoPrev = type("NoPrev", (Exception, ), {})
NoTop = type("NoTop", (Exception, ), {})


async def any_state_except_none_func(_):
    return await fsm.StateCtx.get().get_state() is not None


async def no_state_but_none_func(_):
    return await fsm.StateCtx.get().get_state() is None


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
    def __eq__(
        mcs,
        _s: "Union[M, Container[M], Type[Group], Literal['*']]",
    ) -> Filter:
        if _s == ANY_STATE_EXCEPT_NONE:
            _f = any_state_except_none_func

        elif _s is None:
            _f = no_state_but_none_func

        elif isinstance(_s, type) and issubclass(_s, Group):
            async def _f(_):
                current_state = await fsm.StateCtx.get().get_state()

                for state in _s.all_state_objects:
                    if state.name == current_state:
                        fsm.MCtx.set(state)
                        return True

                return False

        elif isinstance(_s, M):
            async def _f(_):
                current_state = await fsm.StateCtx.get().get_state()
                ok = current_state == _s.name
                if ok:
                    fsm.MCtx.set(_s)
                return ok

        else:
            raise ValueError(
                "`state` parameter must be any of: "
                "`M` object, `Group` class, `None` singleton, \"*\" "
                "(star notation for any state)"
            )

        return Filter(_f, None)

    @classmethod
    def exact(
        mcs,
        state: "Union[M, Container[M], Type[Group], Literal['*']]",
    ) -> Filter:
        # noinspection PyTypeChecker
        return State == state  # type: ignore

    any: Filter = _ilc_descriptor(
        Filter(any_state_except_none_func, event_builder=None)
    )

    entry: Filter = _ilc_descriptor(
        Filter(no_state_but_none_func, event_builder=None)
    )


class State(metaclass=_MetaCurrentState):
    """
    Class with implemented in metaclass magic methods.
    Any state: ANY_STATE states "*". Simply use equality operator to builtin
    methods:
        CurrentState == "*"
        CurrentState.any
    Particular state(s):
        CurrentState == ["state_1", "state_2"]
        CurrentState == "state_1"
    """


class M:
    __slots__ = "name", "owner"

    def __set_name__(self, owner: "_MetaStateGroup", name: str) -> None:
        if not issubclass(owner, Group):
            raise ValueError(
                "State should be declared only in `StateGroup`"
            )

        self.owner = owner
        self.name = owner.__full_group_name__ + name

    def __str__(self) -> str:
        return self.name

    @property
    def next(self) -> "M":
        _oss = self.owner.all_state_objects
        try:
            return _oss[_oss.index(self) + 1]  # type: ignore
        except IndexError:
            raise NoNext from None

    @property
    def prev(self) -> "M":
        _oss = self.owner.all_state_objects
        try:
            return _oss[_oss.index(self) - 1]  # type: ignore
        except IndexError:
            raise NoPrev from None

    @property
    def top(self) -> "M":
        try:
            return self.owner.all_state_objects[0]  # type: ignore
        except IndexError:
            raise NoTop from None


class _MetaStateGroup(type):
    def __new__(
        mcs,
        name: str,
        bases: Tuple[Type[Any], ...],
        namespace: Dict[str, Any],
        **kwargs: Any,
    ) -> "Type[Group]":
        cls = super(_MetaStateGroup, mcs).__new__(
            mcs, name, bases, namespace
        )

        states = []
        children = []

        cls._group_name = name

        for name, prop in namespace.items():
            if isinstance(prop, M):
                states.append(prop)
            elif isinstance(prop, type) and issubclass(prop, Group):
                children.append(prop)
                prop.parent = cls

        cls.parent = None
        cls.children = tuple(children)
        cls.states = tuple(states)

        return cls

    @property
    def __full_group_name__(cls) -> str:
        if cls.parent:
            return ".".join((cls.parent.__full_group_name__, cls._group_name))
        return cls._group_name

    @property
    def all_children(cls) -> "Tuple[Type[Group], ...]":
        result = cls.children
        for child in cls.children:  # type: Group
            result += child.children
        return result

    @property
    def all_state_objects(cls) -> "Tuple[M, ...]":
        result = cls.states
        for child in cls.children:  # type: Group
            result += child.all_state_objects
        return result

    @property
    def all_state_names(cls) -> "Tuple[str, ...]":
        return tuple(state.name for state in cls.all_state_objects)

    def get_root(cls) -> "Type[Group]":
        if cls.parent is None:
            return cast(Type[Group], cls)
        return cls.parent.get_root()

    def __str__(self) -> str:
        return f"<StatesGroup '{self.__full_group_name__}'>"

    @property
    def last(cls) -> str:
        return cls.all_state_names[-1]

    @property
    def first(cls) -> str:
        return cls.all_state_names[0]


class Group(metaclass=_MetaStateGroup):
    """
    todo
    """


__all__ = (
    "State",
    "Group",
    "M",
    "ENTRYPOINT_STATE",
    "ANY_STATE_EXCEPT_NONE",
    "NoTop",
    "NoPrev",
    "NoNext",
)
