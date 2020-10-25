from typing import Protocol

from telethon.events.common import EventCommon

from _garnet.events.handler import EventHandler


class Intermediate(Protocol):
    async def __call__(self, handler: EventHandler, event: EventCommon):
        pass
