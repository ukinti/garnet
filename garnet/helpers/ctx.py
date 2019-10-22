from __future__ import annotations
import typing

# noinspection PyPackageRequirements
import contextvars

Type = typing.TypeVar("Type")


class ContextInstanceMixin:
    def __init_subclass__(cls, **kwargs):
        cls.__ctx_var = contextvars.ContextVar("initialized_" + cls.__name__)
        return cls

    @classmethod
    def current(cls: typing.Type[Type], no_error=True) -> Type:
        if no_error:
            return cls.__ctx_var.get(None)
        return cls.__ctx_var.get()

    @classmethod
    def set_current(cls: typing.Type[Type], value: Type) -> typing.NoReturn:
        if not isinstance(value, cls):
            raise ValueError(f"Got wrong instance, expected {cls!r} got {value!r}")

        cls.__ctx_var.set(value)
