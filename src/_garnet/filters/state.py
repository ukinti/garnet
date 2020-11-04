from typing import (
    Any,
    Container,
    Dict,
    Iterable,
    Literal,
    Tuple,
    Type,
    Union,
    cast,
)

from _garnet.events.filter import Filter
from _garnet.vars import fsm

_DummyGroupT = Iterable[Union[str, int, Any]]  # use Any to allow nested types

ENTRYPOINT_STATE = None
ANY_STATE_EXCEPT_NONE = "*"


class NoNext(Exception):
    """NoNext item in the states group."""


class NoPrev(Exception):
    """NoPrev item in the states group."""


class NoTop(Exception):
    """NoTop item in the states group."""


# region State filter
async def any_state_except_none_func(_):
    return await fsm.CageCtx.get().get_state() is not None


async def no_state_but_none_func(_):
    return await fsm.CageCtx.get().get_state() is None


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
        mcs, _s: "Union[M, Container[M], Type[Group], Literal['*']]",
    ) -> Filter:
        if _s == ANY_STATE_EXCEPT_NONE:
            _f = any_state_except_none_func

        elif _s is None:
            _f = no_state_but_none_func

        elif isinstance(_s, type) and issubclass(_s, Group):

            async def _f(_):
                current_state = await fsm.CageCtx.get().get_state()

                for state in _s.all_state_objects:
                    if state.name == current_state:
                        fsm.MCtx.set(state)
                        return True

                return False

        elif isinstance(_s, M):

            async def _f(_):
                current_state = await fsm.CageCtx.get().get_state()
                ok = current_state == _s.name
                if ok:
                    fsm.MCtx.set(_s)
                return ok

        else:
            raise ValueError(
                "`state` parameter must be any of: "
                '`M` object, `Group` class, `None` singleton, "*" '
                "(star notation for any state)"
            )

        return Filter(_f, None)

    @classmethod
    def exact(
        mcs, state: "Union[M, Container[M], Type[Group], Literal['*']]",
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


# endregion


# region states group
class M:
    """
    Member of states group (fake descriptor).
    Holds reference to its group, its full name,
    next, previously and firstly declared `M`'s

    Usage::
        >>> from garnet.filters.group import M, Group
        >>>
        >>> class MyGroup(Group):
        ...     a = M()
        ...     b = M()
        ...     c = M()
        >>>
        >>> assert MyGroup.a.owner == MyGroup
        >>> assert MyGroup.b.name == "MyGroup.b"
        >>> assert MyGroup.b.next == MyGroup.c
        >>> assert MyGroup.c.top == MyGroup.a
        >>>
        >>> from garnet.filters import group
        >>> try:
        ...     MyGroup.c.next
        ... except group.NoNext:
        ...     raise AssertionError("oopsie-woopsie")
        ...
        oopsie-woopsie
    """

    __slots__ = "_sh_name", "owner"

    def __set_name__(self, owner: "_MetaStateGroup", name: str) -> None:
        if type(owner) != _MetaStateGroup:
            raise ValueError("State should be declared only in `StateGroup`")

        self.owner = owner
        self._sh_name = name

    @property
    def name(self):
        """Get the full name of a member."""
        return ".".join((self.owner.full_group_name, self._sh_name))

    def __str__(self) -> str:
        """Affects str(...M-object...)."""
        return self.name

    @property
    def next(self) -> "M":
        """Get next item of a group which self is in."""
        _oss = self.owner.all_state_objects
        try:
            return _oss[_oss.index(self) + 1]  # type: ignore
        except IndexError:
            raise NoNext from None

    @property
    def prev(self) -> "M":
        """Get previous item of a group which self is in."""
        _oss = self.owner.all_state_objects
        try:
            return _oss[_oss.index(self) - 1]  # type: ignore
        except IndexError:
            raise NoPrev from None

    @property
    def top(self) -> "M":
        """Get the top (head) item of a group which self is in."""
        try:
            return self.owner.all_state_objects[0]  # type: ignore
        except IndexError:
            raise NoTop from None


def is_reserved(name: str, /) -> bool:
    """
    Check if the name is reserved for state group.
    """

    return name in frozenset(
        (
            "parent",
            "children",
            "states",
            "first",
            "last",
            "all_state_names",
            "all_state_objects",
            "all_children",
            "_group_name",
            "full_group_name",
        )
    )


class _MetaStateGroup(type):
    def __new__(
        mcs, name: str, bases: Tuple[Type[Any], ...], namespace: Dict[str, Any],
    ) -> "Type[Group]":
        cls = super(_MetaStateGroup, mcs).__new__(mcs, name, bases, namespace)

        states = []
        children = []

        cls._group_name = name
        dont_ignore_namespace_garbage = namespace.get(
            "__ignore_garbage__", False
        )

        for name, prop in namespace.items():
            if is_reserved(name):
                raise AttributeError(
                    "{name!s} for {cls!r} cannot be set, since it's reserved"
                )

            if isinstance(prop, M):
                states.append(prop)
            elif isinstance(prop, type) and issubclass(prop, Group):
                children.append(prop)
                prop.parent = cls
            elif dont_ignore_namespace_garbage:
                raise TypeError(
                    f"{name!s} is type of {type(prop).__name__}, "
                    f"but only {Group.__name__} classes "
                    f"and {M.__name__} objects are allowed"
                )

        cls.parent = None
        cls.children = tuple(children)
        cls.states = tuple(states)

        return cast(Type[Group], cls)

    @property
    def full_group_name(cls) -> str:
        """Get the full name for states group(include parent classes name)."""
        if cls.parent:
            return ".".join((cls.parent.full_group_name, cls._group_name))
        return cls._group_name

    @property
    def all_children(cls) -> "Tuple[Type[Group], ...]":
        """Get tuple of children groups."""
        result = cls.children
        for child in cls.children:  # type: Type[Group]
            result += child.children
        return result

    @property
    def all_state_objects(cls) -> "Tuple[M, ...]":
        """
        Get tuple of state members including children, excluding parent groups.
        """
        result = cls.states
        for child in cls.children:  # type: Type[Group]
            result += child.all_state_objects
        return result

    @property
    def all_state_names(cls) -> "Tuple[str, ...]":
        """
        Get tuple of names of  state members
        including children, excluding parent groups.
        """
        return tuple(state.name for state in cls.all_state_objects)

    def get_root(cls) -> "Type[Group]":
        """
        Get root of states group.
        If cls is already one or does not know about parent, it returns itself,
        otherwise emits finds to upper parent.
        """
        if cls.parent is None:
            return cast(Type[Group], cls)
        return cls.parent.get_root()

    def __str__(self) -> str:
        """Affects(...Group-class...)"""
        return f"<StatesGroup '{self.full_group_name}'>"

    @property
    def last(cls) -> str:
        """Get the last member of the states group (includes children)."""
        return cls.all_state_names[-1]

    @property
    def first(cls) -> str:
        """Get the first member of the states group (includes children)."""
        return cls.all_state_names[0]

    def from_iter(
        cls,
        iterable: "Union[_DummyGroupT, Iterable[_DummyGroupT]]",
        main_group_name: str = "AnonGroup",
        _depth: int = 0,
        /,
    ) -> "Type[Group]":
        """
        Create "Group" class but from iterable of strings or ints.
        (can be nested iterable of possibly nested iterables)

        :param iterable: pass iterable of iterables or just strings, integers
        :param main_group_name: upper group name (main parent name)
        :param _depth: ignore this attribute unless you know what are you doing
        :return: new group class inheritor class

        Usage::

            >>> from garnet.filters.group import Group
            >>>
            >>> S = Group.from_iter(("a", "b", "c", ("d", "e")))
            >>>
            >>> assert len(S.all_children) == 1
            >>> assert S.all_children[0].parent == S
            >>> assert len(S.all_state_objects) == len("abcde")
            >>> assert len(S.all_children[0].all_state_object) == len("de")
        """

        namespace: Dict[str, Union[M, Type[Group]]] = {}

        for sog in iterable:

            if isinstance(sog, (str, int)):
                namespace[str(sog)] = M()

            elif isinstance(sog, Iterable):
                inner_group_name = (
                    f"{main_group_name}_{_depth+1}{len(namespace)}"
                )

                namespace[inner_group_name] = cls.from_iter(
                    sog, inner_group_name, _depth + 1
                )
            else:
                raise TypeError(
                    f"Expected string or iterable of strings,"
                    f" not {type(sog).__name__}"
                )

        return _MetaStateGroup(  # type: ignore
            main_group_name, (Group,), namespace,
        )


class Group(metaclass=_MetaStateGroup):
    """
    States group base class.

    Usage::

        >>> from garnet.filters.group import Group
        >>>
        >>> class MyGroup(Group):
        ...     pass
        >>>
        >>> assert MyGroup.full_group_name == "MyGroup"
    """


# endregion


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
