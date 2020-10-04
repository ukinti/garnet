import contextvars
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from _garnet.events.fsm_context import FSMContext

StateCtx: "contextvars.ContextVar[FSMContext]" = contextvars.ContextVar(
    "StateCtx"
)
