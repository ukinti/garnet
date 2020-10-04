from __future__ import annotations

import contextvars
from typing import Any, ClassVar, Generic, Optional, TypeVar, cast

ContextInstance = TypeVar("ContextInstance")


class ContextInstanceMixin(Generic[ContextInstance]):
    __context_instance: ClassVar[contextvars.ContextVar[ContextInstance]]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        super().__init_subclass__(**kwargs)
        cls.__context_instance = contextvars.ContextVar(
            f"instance_{cls.__name__}"
        )

    @classmethod
    def get_current(cls, no_error: bool = False) -> Optional[ContextInstance]:
        cls.__context_instance = cast(
            contextvars.ContextVar[ContextInstance], cls.__context_instance
        )

        try:
            current: Optional[ContextInstance] = cls.__context_instance.get()
        except LookupError:
            if no_error:
                current = None
            else:
                raise

        return current

    @classmethod
    def set_current(
        cls, value: ContextInstance
    ) -> contextvars.Token[ContextInstance]:
        if not isinstance(value, cls):
            raise TypeError(
                f"Value should be instance of {cls.__name__!r} not {type(value).__name__!r}"
            )
        return cls.__context_instance.set(value)

    @classmethod
    def reset_current(cls, token: contextvars.Token[ContextInstance]) -> None:
        cls.__context_instance.reset(token)
