import contextvars
from typing import TYPE_CHECKING, Any, Optional

if TYPE_CHECKING:
    from _garnet.events.user_cage import UserCage
    from _garnet.filters.state import M

CageCtx: "contextvars.ContextVar[UserCage[Any]]" = contextvars.ContextVar(
    "user_cage"
)
MCtx: "contextvars.ContextVar[Optional[M]]" = contextvars.ContextVar(
    "m", default=None,
)
