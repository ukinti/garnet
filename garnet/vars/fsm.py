import contextvars

from garnet.storages.base import FSMContext

State: contextvars.ContextVar[FSMContext] = contextvars.ContextVar("State")
