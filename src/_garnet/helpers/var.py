from typing import Generic, Optional, Type, TypeVar

VT = TypeVar("VT")
InstanceT = TypeVar("InstanceT")


class Var(Generic[InstanceT, VT]):
    __slots__ = ("value",)

    def __init__(self, value: Optional[VT] = None) -> None:
        self.value = value

    def __set_name__(self, owner: Type[InstanceT], val: VT) -> None:
        if self.value is None:
            self.value = val

    def __get__(
        self, instance: Optional[InstanceT], owner: Optional[Type[InstanceT]],
    ) -> Optional[VT]:
        return self.value
