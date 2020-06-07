Garnet
===========

Garnet — bot-friendly telethon
********************************

.. invisible-content-till-nel
.. _aioredis: https://github.com/aio-libs/aioredis
.. _cryptg: https://pypi.org/project/cryptg/
.. _telethon: https://pypi.org/project/Telethon/
.. _orjson: https://pypi.org/project/orjson/
.. _ujson: https://pypi.org/project/ujson/
.. _hachoir: https://pypi.org/project/hachoir/
.. _aiohttp: https://pypi.org/project/aiohttp/
.. _Alex: https://github.com/JrooTJunior

.. image:: https://raw.githubusercontent.com/uwinx/garnet/master/static/pomegranate.jpg


************
Installation
************

    pip install telegram-garnet


^^^^^^^
Extras
^^^^^^^
- ``aioredis`` - redis driver required if you're using RedisStorage* aioredis_
- ``orjson`` or ``ujson`` - RedisStorage/JSONStorage not required at all (ser/deser)ialization orjson_ ujson_


****************************
🌚 🌝 FSM-Storage types
****************************


- File - json storage, the main idea behind JSON storage is a custom reload of file and usage of memory session for writing, so the data in json storage not always actual

- Memory - powerful in-memory map<str> based storage, only thing - not persistent

- Redis - (requires aioredis_) - redis is fast key-value storage, if you're using your data is durable and persistent


Pomegranate implements updates dispatching and checks callback's filters wrapping all callbacks into ``garnet::Callback`` object

***********************
😋 Filters
***********************

``Filter`` object is the essential part of Pomegranate, the do state checking and other stuff.

Basically, it's ``func`` from ``MyEventBuilder(func=lambda self: <bool>)`` but a way more complicated and not stored in EventBuilder, it's stored in callback object


Filters support bitwise operations ::

    # & (conjunction), | (disjunction), ~ (inversion), ^ (exclusive disjunction)
    # also: ==, != (idk why)
    @bot.on(MessageText.exact(".") | MessageText.exact(".."))


^^^^^^^^^^^^^^^^^^^^^^^
📨 Messages
^^^^^^^^^^^^^^^^^^^^^^^

`Following examples will include pattern`


.. code:: python

    from garnet import MessageText, TelegramClient
    bot = TelegramClient.from_env().start_as_bot()

    # // our code here //

    bot.run_until_disconnected()

.. code:: python

    # handling /start and /help
    @bot.on(MessageText.commands("help", "start"))
    async def cmd_handler(message: custom.Message):
        await message.reply("Hey there!")

    # handling exact words
    my_secret = "abcxyz"
    @bot.on(MessageText.exact(my_secret))
    async def secret_handler(message: custom.Message):
        await message.reply("Secret entered correctly! Welcome!")

MessageText or text(``from garnet import text``) includes following comparisons all returning <bool>
 - ``.exact(x)`` -> ``event.raw_text == x``
 - ``.commands(*x)`` -> ``event.raw_text.split()[0][1:] in x``
 - ``.match(x)`` -> ``re.compile(x).match(event.raw_text)``
 - ``.between(*x)`` -> ``event.raw_text in x``
 - ``.isdigit()`` -> ``(event.raw_text or "").isdigit()``
 - ``.startswith(x)`` -> ``event.raw_text.startswith(x)``


``Len`` attribute in ``MessageText`` which has cmp methods::


    @bot.on((MessageText.Len <= 14) | (MessageText.Len >= 88))



^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
👀 CurrentState class
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

``from garnet import CurrentState``


Once great minds decided that state checking will be in filters without adding ``state`` as handler decorator parameter and further storing state in ``callback.(arg)``
``CurrentState`` class methods return ``Filter``. There are two problems that Filter object really solves, ``Filter``'s function can be any kind of callable(async,sync), filters also have a flag ``requires_context``, FSMProxy is passed if true

See `FSM example <https://github.com/uwinx/garnet/blob/master/examples/fsm.py>`_ to understand how CurrentState works

Includes following methods all returning <bool>
 - ``.exact(x)`` or ``CurrentState == x`` -> ``await context.get_state() == x``
 - ``CurrentState == [x, y, z]`` -> ``await context.get_state() in [x, y, z]``
 - ``CurrentState == all`` or ``CurrentState == any`` -> ``await context.get_state() is not None``

^^^^^^^^^^^^^^^^^^^^^^^^^^^
🦔 Custom Filter
^^^^^^^^^^^^^^^^^^^^^^^^^^^

If you want to write your own filter, do it.


.. code:: python

    from garnet import Filter, FSMProxy

    async def myFunc(event): ...
    async def myFuncContextRequires(event, context: FSMProxy): ...
    def normal_func(event): ...

    @bot.on(Filter(normal_func), Filter(myFunc), Filter(myFuncContextRequires, requires_context=True))
    async def handler(event, context: FSMProxy): ...
    # same as
    @bot.on(normal_func, myFunc, Filter(myFuncContextRequires, requires_context=True))
    async def handler(event): ...

So the handler can take strict ``context`` argument and also ignore it

^^^^
Also
^^^^

There're file extension filters in ``garnet.filters.file_ext::File``, import as ``from garnet.filters import File``

Some of filters are ported from ``telethon.utils`` as ``File.is_gif``, ``Filter.is_audio``, ``Filter.is_image``, ``Filter.is_video``

And bunch of file extensions such as ``File.png``, ``File.ogg`` which are filters.


*****************************
On start|finish|background
*****************************

``garnet::TelegramClient`` contains three lists on_start on_background and on_finish, their instance is ``PseudoFrozenList`` which freezes at calling ``.run_until_disconnected``
``PseudoFrozenList`` has three main methods::

    .append(*items)
    .remove(*items)
    .freeze()
    .__call__() => (func) => (wrapped_func)   # for shiny decorator

``items`` in case of TelegramClient means unpacked container of async-defined functions taking on position arguments

**Usage:**


.. code-block:: python

    # my_module.py
    class MyPostgresDatabase:
        ...
        async def close_pool(self, bot): await self.pool.safe_close()
        async def open_pool(self, bot): await self.pool.open_conn_pool()

    # garnethon.py
    from garnet import TelegramClient
    from my_module import MyPostgresDatabase

    db = MyPostgresDatabase()
    bot = TelegramClient.from_env().start_as_bot()
    bot.on_start.append(db.open_pool)
    bot.on_finish.append(db.close_pool)
    ...

    @bot.on_background()
    async def xyz(cl: TelegramClient):
        while True:
           ...

    bot.run_until_connected()


****************************************************
📦 Router and Migrating to garnet using Router
****************************************************

Think of router as just a dummy container of handlers(callbacks)

`garnet::router::Router` may be helpful if you have telethon's `event.register` registered handlers. One thing: Router, I believe, is correct and more obvious way of registering event handlers. Example:

**Migrate from telethon to garnet, also use for bot.on cases(soon better example)**

.. code-block:: python

    # my_handlers.py

    # telethon register(bad) will raise Warning in garnet
    from telethon import events

    @events.register(event_type)
    async def handler(event): ...

    # garnet's telethon-like router
    from garnet.router import TelethonRouter

    router = TelethonRouter()

    @router(event_type)
    async def handler(event): ...



The advantage of routers is evidence of registering handlers when you have module-separated handlers. `events.register` was doing well, but blindly importing modules to register handlers and don't use them(modules) doesn't seem like a good idea.

**Example of registering router in bot application**

.. code-block:: python

    # handlers/messages.py
    from garnet.router import Router

    router = Router()

    @router()
    async def handler(event): ...

    # handlers/cb_query.py
    from garnet.events import CallbackQuery
    from garnet.router import Router

    router = Router()

    @router(event=CallbackQuery())
    async def handler(event): ...

    # entry.py ()
    from garnet import TelegramClient

    from handlers import messages, cb_query

    tg = TelegramClient.from_env().start_as_bot()
    tg.bind_routers(messages, cb_query)
    ...

``TelethonRouter`` and ``Router`` both have following methods:

::

    .message_handler(*filters)
    .callback_query_handler(*filters)
    .chat_action_handler(*filters)
    .message_edited_handler(*filters)
    .album_handler(*filters)

*********************
🍬 Context magic
*********************

One of the sweetest parts of garnet. Using `contextvars` we reach incredibly beautiful code :D
*this is not FSMContext don't confuse with context magic provided by contextvars*

As an example, bot that doesn't requires `TelegramClient` to answer messages directly.

.. code-block:: python

    from garnet.functions.messages import reply, message, respond

    @bot.message_handler()
    async def handler():
        # message() - function to get current Message event
        await message().respond("ok")
        await message().reply("ok")
        # the same result, but shortcuts
        await respond("ok")
        await reply("Ok")


``garnet.functions.messages`` contains ``current`` class with handy shortcuts:

.. code-block:: python

    from garnet.functions.messages import current

    current.text  # raw text
    current.fmt_text  # formatted text according to default parse mode
    current.chat  # current chat
    current.chat_id  # current chat identifier


******************
What's more ❓
******************

1. ``garner.client::TelegramClient.conf`` is an attribute for your stuff you should share "globally". Be careful using it.



2. Garnet can patch ``TLRequest.__await__`` method. To do something like:

.. code-block:: python

    from garnet.patch_tl_methods import install
    from telethon.tl.functions.users import GetUsersRequest

    install()

    for user in await GetUsersRequest(["martin_winks", "YOURUSERNAME"]):
        print(user.username)


Just to have fun with debugging something with raw API.

*******************
Contacts/Community
*******************

You can find me on telegram by `@martin_winks <https://telegram.me/martin_winks>`_

Our small telegram `group <https://t.me/joinchat/B2cC_hknbKGm3_G8N9qifQ>`_

**********************
🤗 Credits
**********************

Finite-state machine was ported from cool BotAPI library 'aiogram', special thanks to Alex_

Support lonamiwebs: `lonamiwebs <http://paypal.me/lonamiwebs>`_

Support aiogram project: `JRootJunior <https://opencollective.com/aiogram/organization/0/website>`_
