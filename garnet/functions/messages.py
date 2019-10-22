import typing

from telethon import hints, types, custom

from ..events.newmessage import NewMessage


def message() -> custom.Message:
    # noinspection PyTypeChecker
    return NewMessage.Event.current()  # type: ignore


# noinspection PyPep8Naming
class current(object):
    @property
    def chat_id(*self) -> typing.Union[type(None), int]:
        """
        get current chat's ID
        """
        return message().chat_id

    @property
    def chat(*self) -> typing.Union[types.User, types.Chat, types.Channel]:
        """
        get current chat
        """
        return message().chat


async def respond(
        message_: 'hints.MessageLike' = '',
        *,
        reply_to: 'typing.Union[int, types.Message]' = None,
        parse_mode: typing.Optional[str] = (),
        link_preview: bool = True,
        file: 'typing.Union[hints.FileLike, typing.Sequence[hints.FileLike]]' = None,
        force_document: bool = False,
        clear_draft: bool = False,
        buttons: 'hints.MarkupLike' = None,
        silent: bool = None,
        schedule: 'hints.DateLike' = None
        ) -> 'types.Message':

    return await message().respond(**locals())


async def reply(
        message_: 'hints.MessageLike' = '',
        *,
        reply_to: 'typing.Union[int, types.Message]' = None,
        parse_mode: typing.Optional[str] = (),
        link_preview: bool = True,
        file: 'typing.Union[hints.FileLike, typing.Sequence[hints.FileLike]]' = None,
        force_document: bool = False,
        clear_draft: bool = False,
        buttons: 'hints.MarkupLike' = None,
        silent: bool = None,
        schedule: 'hints.DateLike' = None
        ) -> 'types.Message':

    return await message().reply(**locals())


__all__ = (
    "current", "reply", "respond", "message"
)
