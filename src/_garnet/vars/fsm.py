import contextvars
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from _garnet.events.fsm_context import FSMContext
    from _garnet.filters.state import M

StateCtx: "contextvars.ContextVar[FSMContext]" = contextvars.ContextVar(
    "user_state"
)
MCtx: "contextvars.ContextVar[Optional[M]]" = contextvars.ContextVar(
    "m", default=None,
)
