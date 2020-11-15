from contextvars import ContextVar
from typing import Dict, Optional, TypeVar
from typing import cast as t_cast

T = TypeVar("T")

Query: ContextVar[Dict[str, str]] = ContextVar("query")


def casted(__t: Optional[T] = None, default: Optional[T] = None) -> T:
    return t_cast(T, Query.get(default))  # type: ignore
