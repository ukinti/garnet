🍷 Pomegranate a.k.a garnet
===================================

As good as pomegranate wine.
-----------------------------------

.. invisible-content-till-nel
.. _aioredis: https://github.com/aio-libs/aioredis
.. _cryptg: https://pypi.org/project/cryptg/
.. _telethon: https://pypi.org/project/Telethon/
.. _orjson: https://pypi.org/project/orjson/
.. _ujson: https://pypi.org/project/ujson/
.. _hachoir: https://pypi.org/project/hachoir/
.. _aiohttp: https://pypi.org/project/aiohttp/
.. _Alex: https://github.com/JrooTJunior

.. image:: https://raw.githubusercontent.com/uwinx/pomegranate/master/static/pomegranate.jpg

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
    :target: https://github.com/python/black
    :alt: aioqiwi-code-style


Install::

    pip install "https://github.com/uwinx/pomegranate/archive/master.zip"


**Dependencies:**
    - ``telethon`` - main dependency telethon_
    - ``aioredis`` - redis driver if you use RedisStorage* aioredis_
    - ``orjson`` || ``ujson`` - RedisStorage/JSONStorage de-&& serialization orjson_ ujson_
    - ``cryptg``, ``hachoir``, ``aiohttp`` - boost telethon itself cryptg_ hachoir_ aiohttp_

---------------------------------
🌚 🌝 FSM-Storage types
---------------------------------

- File - json storage, the main idea behind JSON storage is a custom reload of file and usage of memory session for writing, so the data in json storage not always actual

- Memory - powerful in-memory map<str> based storage, only thing - not persistent

- Redis - (requires aioredis_) - redis is fast key-value storage, if you're using your data is durable and persistent


Pomegranate implements updates dispatching and checks callback's filters wrapping all callbacks into ``garnet::Callback`` object

----------------
😋 Filters
----------------

``Filter`` object is the essential part of Pomegranate, the do state checking and other stuff.

Basically, it's ``func`` from ``MyEventBuilder(func=lambda _: <bool>)`` but a way more complicated and not stored in EventBuilder, it's stored in callback object


Useful filters

1) 📨 **Messages**


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

MessageText includes following comparisons all returning <bool>
 - ``.exact(x)`` -> ``event.raw_text == x``
 - ``.commands(*x)`` -> ``event.raw_text.split()[0][1:] in x``
 - ``.match(x)`` -> ``re.compile(x).match(event.raw_text)``
 - ``.between(*x)`` -> ``event.raw_text in x``
 - ``.isdigit()`` -> ``(event.raw_text or "").isdigit()``
 - ``.startswith(x)`` -> ``event.raw_text.startswith(x)``



2) 👀 **state module**  [``from garnet import state``]

Once great minds decided that state checking will be in filters without adding ``state`` to on func params and further storing state in ``callback.(arg)``
``state`` module methods return ``Filter`` as well. There are two problems that Filter object really solves, ``Filter``'s function can be any kind of callable(async,sync), filters also have a flag ``requires_context``, FSMProxy is passed if true

See `FSM example <https://github.com/uwinx/pomegranate/blob/master/examples/fsm.py>`_ to understand how CurrentState works

Includes following methods all returning <bool>
 - ``.exact(x)`` -> ``await context.get_state() == x``
 - ``.between(x)`` -> ``await context.get_state() in x``
 - ``.equal(x)`` -> ``.exact(x)``
 - ``.not_equal(x)`` -> ``!.exact(x)``
 - ``.every()`` -> ``(await context.get_state) is not None``


3) 🦔 Custom **Filter**

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


=================
🐙 Easy handlers
=================

``garnet::TelegramClient`` has several handlers::


    .message_handler(*f)
    .callback_query_handler(*f)
    .chat_action_handler(*f)
    .message_edited_handler(*f)
    .album_handler(*f):


======================
On start|finish
======================

``garnet::TelegramClient`` contains two lists on_start and on_finish, their instance is ``PseudoFrozenList`` which freezes at calling ``.run_until_disconnected``
``PseudoFrozenList`` has three main methods::

    .append(*coro)
    .remove(*coro)
    .freeze()

Where coro is async-defined function which takes one positional argument, its instance will be TelegramClient

Usage example:

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
    bot.run_until_connected()

=================
What's more ❓
=================

Class-based handlers are also can be implemented with garnet conveniently. Use your imagination and ``garnet::callbacks::base::Callback`` as a parent class

Pretty bitwise operation supported filters(I highly recommend to use them)::

    # &, |, ~, ^
    # also: ==, != (idk why)
    @bot.on(MessageText.exact(".") | MessageText.exact(".."))


``Len`` attribute in ``MessageText`` which has cmp methods::


    @bot.on((MessageText.Len <= 14) | (MessageText.Len >= 88))


=====================
🤗 Credits
=====================

Finite-state machine was ported from cool BotAPI library 'aiogram', special thanks to Alex_
