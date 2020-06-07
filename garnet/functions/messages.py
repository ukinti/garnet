import typing

from telethon import hints, types, custom

from garnet.events import NewMessage


VT_co = typing.TypeVar("VT_co")


def message() -> custom.Message:
    # noinspection PyTypeChecker
    return NewMessage.Event.current()  # type: ignore


class _CurrentClsDescriptor(typing.Generic[VT_co]):
    __slots__ = ("_fget",)

    def __init__(self, fget: typing.Callable[[], VT_co]):
        self._fget = fget

    def __get__(self, *_) -> VT_co:
        return self._fget()  # type: VT_co


# noinspection PyPep8Naming
class current:
    chat_id: _CurrentClsDescriptor[typing.Optional[int]] = _CurrentClsDescriptor(
        lambda: message().chat_id
    )
    """get current chat id"""

    chat: _CurrentClsDescriptor[
        typing.Union[types.User, types.Chat, types.Channel]
    ] = _CurrentClsDescriptor(lambda: message().chat)
    "get current chat"

    fmt_text: _CurrentClsDescriptor[typing.Optional[str]] = _CurrentClsDescriptor(
        lambda: message().text
    )
    """get formatted text with respect to current parse_mode e.g. <code>...</code>"""

    text: _CurrentClsDescriptor[typing.Optional[str]] = _CurrentClsDescriptor(
        lambda: message().raw_text
    )
    """get the raw text from message"""


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
