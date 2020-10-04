import contextlib
import contextvars
from typing import Optional, Union

from telethon.tl.custom.chatgetter import ChatGetter
from telethon.tl.custom.sendergetter import SenderGetter

UserIDCtx: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "CurrentUser", default=None
)
ChatIDCtx: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "CurrentChat", default=None
)


@contextlib.contextmanager
def current_user_and_chat_ctx_manager(event: Union[SenderGetter, ChatGetter]):
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
