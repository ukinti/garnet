import contextlib
import contextvars
from typing import Generator, Optional, Union

from telethon.tl.custom.chatgetter import ChatGetter
from telethon.tl.custom.sendergetter import SenderGetter

UserIDCtx: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "user_id", default=None
)
ChatIDCtx: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "chat_id", default=None
)


@contextlib.contextmanager
def current_user_and_chat_ctx_manager(
    event: Union[SenderGetter, ChatGetter]
) -> Generator[None, None, None]:
    user_token = UserIDCtx.set(None)
    chat_token = ChatIDCtx.set(None)

    try:
        if isinstance(event, SenderGetter):
            user_token = UserIDCtx.set(event.sender_id)
        if isinstance(event, ChatGetter):
            chat_token = ChatIDCtx.set(event.chat_id)
        yield

    finally:
        UserIDCtx.reset(user_token)
        ChatIDCtx.reset(chat_token)
