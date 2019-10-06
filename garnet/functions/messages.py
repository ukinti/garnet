import typing

from telethon import hints, types, custom

from ..events.newmessage import NewMessage


def event() -> custom.Message:
    # noinspection PyTypeChecker
    return NewMessage.Event.current()  # type: ignore


async def respond(
        message: 'hints.MessageLike' = '',
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

    return await event().respond(**locals())


async def reply(
        message: 'hints.MessageLike' = '',
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

    return await event().reply(**locals())
