import typing

from telethon import hints, types, custom

from garnet.events import NewMessage


def message() -> custom.Message:
    # noinspection PyTypeChecker
    return NewMessage.Event.current()  # type: ignore


# noinspection PyPep8Naming
class current(object):  # type: ignore
    @property
    def chat_id(self) -> typing.Optional[int]:
        """
        get current chat's ID
        """
        return message().chat_id

    @property
    def chat(self) -> typing.Union[types.User, types.Chat, types.Channel]:
        """
        get current chat
        """
        return message().chat

    @property
    def fmt_text(self) -> typing.Optional[str]:
        """
        Get formatted text with respect to current parse_mode
        e.g. <code>...</code>
        """
        return message().text

    @property
    def text(self) -> typing.Optional[str]:
        """
        Get RAW text from update, text without formatting
        """
        return message().raw_text


async def respond(
    message_: "hints.MessageLike" = "",
    *,
    reply_to: "typing.Union[int, types.Message]" = None,
    parse_mode: typing.Optional[str] = (),
    link_preview: bool = True,
    file: "typing.Union[hints.FileLike, typing.Sequence[hints.FileLike]]" = None,
    force_document: bool = False,
    clear_draft: bool = False,
    buttons: "hints.MarkupLike" = None,
    silent: bool = None,
    schedule: "hints.DateLike" = None
) -> "types.Message":

    _l = locals()
    _l["message"] = _l.pop("message_")
    return await message().respond(**locals())


async def reply(
    message_: "hints.MessageLike" = "",
    *,
    reply_to: "typing.Union[int, types.Message]" = None,
    parse_mode: typing.Optional[str] = (),
    link_preview: bool = True,
    file: "typing.Union[hints.FileLike, typing.Sequence[hints.FileLike]]" = None,
    force_document: bool = False,
    clear_draft: bool = False,
    buttons: "hints.MarkupLike" = None,
    silent: bool = None,
    schedule: "hints.DateLike" = None
) -> "types.Message":

    _l = locals()
    _l["message"] = _l.pop("message_")
    return await message().reply(**_l)


__all__ = ("current", "reply", "respond", "message")
