from typing import Type, TypeVar

from telethon.events.album import Album
from telethon.events.callbackquery import CallbackQuery
from telethon.events.chataction import ChatAction
from telethon.events.inlinequery import InlineQuery
from telethon.events.messagedeleted import MessageDeleted
from telethon.events.messageedited import MessageEdited
from telethon.events.messageread import MessageRead
from telethon.events.newmessage import NewMessage
from telethon.events.userupdate import UserUpdate

from _garnet.helpers import ctx as _ctx

InstanceT = TypeVar("InstanceT")


def patch_event_ctx() -> None:
    def ctx_proxy(cls: Type[InstanceT]) -> Type[InstanceT]:
        return type(cls.__name__, (cls, _ctx.ContextInstanceMixin), {})

    Album.Event = ctx_proxy(Album.Event)
    ChatAction.Event = ctx_proxy(ChatAction.Event)
    MessageDeleted.Event = ctx_proxy(MessageDeleted.Event)
    MessageEdited.Event = ctx_proxy(MessageEdited.Event)
    MessageRead.Event = ctx_proxy(MessageRead.Event)
    NewMessage.Event = ctx_proxy(NewMessage.Event)
    UserUpdate.Event = ctx_proxy(UserUpdate.Event)
    CallbackQuery.Event = ctx_proxy(CallbackQuery.Event)
    InlineQuery.Event = ctx_proxy(InlineQuery.Event)


patch_event_ctx()


class StopPropagation(Exception):
    """
    If this exception is raised in any of the handlers for a given event,
    it will stop the execution of all other registered event handlers.
    """


class SkipHandler(Exception):
    """
    If this exception is raised in any of the handlers for a given event,
    it will skip this handler execution and go to the next handler.
    """
