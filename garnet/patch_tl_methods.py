from telethon.tl.functions import TLRequest
from garnet.client import TelegramClient


def _g_await(self):
    client = TelegramClient.current(no_error=False)

    return client.__call__(self, ordered=False).__await__()


def install():
    TLRequest.__await__ = _g_await
