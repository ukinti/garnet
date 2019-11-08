# MIT / Copyright (c) 2016-2019 LonamiWebs

from .common import EventCommon


class EventBuilderDict:
    """
    Helper "dictionary" to return events from types and cache them.
    """
    def __init__(self, client: 'TelegramClient', update, others):
        self.client = client
        self.update = update
        self.others = others

    def __getitem__(self, builder):
        try:
            return self.__dict__[builder]
        except KeyError:
            event = self.__dict__[builder] = builder.build(
                self.update, self.others, self.client._self_input_peer.user_id)

            if isinstance(event, EventCommon):
                event.original_update = self.update
                event._entities = self.update._entities
                event._set_client(self.client)
            elif event:
                event._client = self.client

            return event
