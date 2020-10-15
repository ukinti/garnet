
garnet
######

About
*****

garnet is a ridiculously simple library created mainly for managing your stateful telegram bots written with Telethon.

.. invisible-content-till-nel
.. _aioredis: https://github.com/aio-libs/aioredis
.. _telethon: https://pypi.org/project/Telethon/
.. _Alex: https://github.com/JrooTJunior


***************
How to install?
***************

Although, garnet is ``garnet``, it is named ``telegram-garnet`` on the PyPI, you'll have to tell that to pip.

``pip install telegram-garnet``


*************
Let's dive in
*************

.. code:: python

    # export GARNET_BOT_TOKEN environmental variable

    from garnet import (
        Router, EventDispatcher,
        TelegramClient, Runner,
        events, filters, storages, ctx,
    )

    router = Router(events.NewMessage)

    @router.default(filters.text.commands("start"))
    async def handle_start(event):
        await event.reply(f"Hello, uid={ctx.ChatIDCtx.get()}! I'm from garnet.")

    async def main():
        client = TelegramClient(:session:, :api_id:, :api_hash:)
        event_dp = EventDispatcher(storages.MemoryStorage(), (router, ))
        runner = Runner(event_dp, client)
        await runner.run_blocking()

    if __name__ == "__main__":
        import asyncio
        asyncio.run(main())


************
Key features
************

Filters
=======

Basically ``Filter`` is a "lazy" callable which holds an optional single-parameter function.
Filters are event naive and event aware. Filters are mutable, they can migrate from event-naive to event-aware in garnet.

Public methods
--------------

- ``.is_event_naive -> bool``
- ``.call(e: T, /) -> Awaitable[bool]``

Initializer
^^^^^^^^^^^

``Filter(function[, event_builder])``

Value of the parameter ``function`` must be function that takes exactly one argument with type `Optional[Some]` and
returns ``bool`` either True or False.

Possible operations on Filter instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(those are, primarily logical operators)

Binary
""""""

- ``&`` is a logical AND for two filters
- ``|`` is a logical OR for two filters
- ``^`` is a logical XOR for two filters

Unary
"""""

- ``~`` is a logical NOT for a filter

Examples
---------

.. code:: python3

    from garnet import Filter, events

    async def fun(_): ...

    # example of event aware filter
    Filter(fun, events.NewMessage)

    # example of event-naive
    Filter(fun)

By default ``Filter`` is event-naive, however when using with ``garnet::Router`` for handlers it may be changed.

Filters "from the box"
----------------------

Text filters
^^^^^^^^^^^^

Operations on ``Filter((e: Some) -> bool); Some.raw_text or Some.text``

Import
""""""

``from garnet.filters import text``

Little journey
""""""""""""""

- ``text.Len`` is a special class for ``len(Some.raw_text ... "")`` operations. Supports logical comparison operations, such are ``==``, ``>``, ``>=``, ``<``, ``<=``

- ``text.startswith(prefix: str, /)`` will evaluates to ``Some.raw_text.startswith(prefix)``

- ``text.commands(*cmds: str, prefixes="/", to_set=True)`` will evaluate to check if command is within ``cmd`` (ignores mentions, and works on `Some.text`)

- ``text.match(rexpr: str, flags=0, /)`` will evaluate to ``re.compile(rexpr, flags).match(Some.raw_text)``

- ``text.between(*texts: str, to_set=True)`` will evaluate to ``Some.raw_text in texts``

- ``text.can_be_int(base=10)`` will evaluate to ``try{int(Some.raw_text);return True;}except(ValueError){return False;}``

- ``text.can_be_float()`` similarly to ``text.can_be_int`` but for floats.


Routers
=======

Router (routing table) is a collection of handlers.

Public methods
--------------

Those consist mainly from decorators.

Initializer
^^^^^^^^^^^

``Router(default_event=None, *filters)``

- ``default_event`` default event builder for router
- ``*filters`` router filters, in order to get into handlers, event should pass these filters.

Decorators
^^^^^^^^^^

Depending on ``event_builder`` of a decorator, filters inherit that event builder mutating themselves.

- ``.default(*filters)`` event builder is default Router(**this**, ...), should not be None, must implement ``telethon.common::EventBuilder``

- ``.message(*filters)`` shortcut decorator for event builder ``garnet.events::NewMessage``

- ``.callback_query(*filters)`` shortcut decorator for event builder ``garnet.events::CallbackQuery``

- ``.chat_action(*filters)`` shortcut decorator for event builder ``garnet.events::ChatAction``

- ``.message_edited(*filters)`` shortcut decorator for event builder ``garnet.events::MessageEdited``

- ``on(event_builder, /, *filters)`` pass any event builder (preferably from ``garnet.events::*``)


etc.
^^^^

- ``.register(handler, filters, event_builder)`` register handler with binding filters and event_builder to it.


Examples
--------

.. code:: python

    from garnet import Router, events, Filter

    router = Router(events.NewMessage, Filter(lambda _: True), Filter(lambda _: True))

    @router.default(Filter(lambda _: True))
    async def handler(_): pass


Context variables
=================

``from garnet.ctx import UserIDCtx, ChatIDCtx, StateCtx``


Usual contextual variables, with ``.get()``, ``.set()``, ``.reset()`` methods. You'll always end up using ``.get()``.
Work with those only in handlers.

Also every event builder in ``garnet.events`` is "contextfull", but for ``get``,``set``,``reset`` you shall add ``_current``
postfix.

Notes
-----

Try to use context variables everywhere not depending on other mechanisms, because they work as you want.

*******************
Contacts/Community
*******************

You can find me on telegram by `@martin_winks <https://telegram.me/martin_winks>`_

Our small telegram `group <https://t.me/joinchat/B2cC_hknbKGm3_G8N9qifQ>`_


*******
Credits
*******

Finite-state machine was ported from cool BotAPI library 'aiogram', special thanks to Alex_

- LonamiWebs (Telethon): `lonamiwebs <http://paypal.me/lonamiwebs>`_
- aiogram project: `JRootJunior <https://opencollective.com/aiogram/organization/0/website>`_
