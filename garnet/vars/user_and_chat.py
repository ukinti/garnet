import contextlib
import contextvars
from typing import Optional, Union

from telethon.tl.custom.chatgetter import ChatGetter
from telethon.tl.custom.sendergetter import SenderGetter

UserID: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "CurrentUser", default=None
)
ChatID: contextvars.ContextVar[Optional[int]] = contextvars.ContextVar(
    "CurrentChat", default=None
)


@contextlib.contextmanager
def current_user_and_chat_ctx_manager(event: Union[SenderGetter, ChatGetter]):
    user_token = UserID.set(None)
    chat_token = ChatID.set(None)

    try:
        if isinstance(event, SenderGetter):
            user_token = UserID.set(event.sender_id)
        if isinstance(event, ChatGetter):
            chat_token = ChatID.set(event.chat_id)
        yield

    finally:
        UserID.reset(user_token)
        ChatID.reset(chat_token)
