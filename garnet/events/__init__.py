from typing import Type

from telethon.events.raw import Raw
from telethon.events.album import Album
from telethon.events.chataction import ChatAction
from telethon.events.messagedeleted import MessageDeleted
from telethon.events.messageedited import MessageEdited
from telethon.events.messageread import MessageRead
from telethon.events.newmessage import NewMessage
from telethon.events.userupdate import UserUpdate
from telethon.events.callbackquery import CallbackQuery
from telethon.events.inlinequery import InlineQuery

from ..helpers import ctx as _ctx


def patch_event_ctx():
    def ctx_proxy(cls: Type) -> Type:
        def __init__(self, *args, **kwargs):
            cls.__init__(self, *args, **kwargs)
            self.set_current(self)

        return type(
            cls.__name__, (cls, _ctx.ContextInstanceMixin), {"__init__": __init__}
        )

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


class EventBuilderDict:
    """
    Helper "dictionary" to return events from types and cache them.
    """
    from telethon.events.common import EventCommon  # noqa

    def __init__(self, client, update, others):
        self.client = client
        self.update = update
        self.others = others

    def __getitem__(self, builder):
        try:
            return self.__dict__[builder]
        except KeyError:
            event = self.__dict__[builder] = builder.build(
                self.update, self.others, self.client._self_input_peer.user_id
            )

            if isinstance(event, EventBuilderDict.EventCommon):
                event.original_update = self.update
                event._entities = self.update._entities
                event._set_client(self.client)
            elif event:
                event._client = self.client

            return event


__all__ = (
    "Raw",
    "Album",
    "ChatAction",
    "MessageDeleted",
    "MessageEdited",
    "MessageRead",
    "NewMessage",
    "UserUpdate",
    "CallbackQuery",
    "InlineQuery",
    "EventBuilderDict",
    "StopPropagation",
)


class StopPropagation(Exception):
    """
    If this exception is raised in any of the handlers for a given event,
    it will stop the execution of all other registered event handlers.
    It can be seen as the ``StopIteration`` in a for loop but for events.

    Example usage:

        >>> from telethon import TelegramClient, events
        >>> client = TelegramClient(...)
        >>>
        >>> @client.on(events.NewMessage)
        ... async def delete(event):
        ...     await event.delete()
        ...     # No other event handler will have a chance to handle this event
        ...     raise StopPropagation
        ...
        >>> @client.on(events.NewMessage)
        ... async def _(event):
        ...     # Will never be reached, because it is the second handler
        ...     pass
    """

    # For some reason Sphinx wants the silly >>> or
    # it will show warnings and look bad when generated.
    pass
