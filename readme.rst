
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


****************
🔑 Key features
****************

🔫 Filters
==========

Basically ``Filter`` is a "lazy" callable which holds an optional single-parameter function.
Filters are event naive and event aware.

Public methods
--------------

``.is_event_naive -> bool``

``.call(e: T, /) -> Awaitable[bool]``

Initializer
^^^^^^^^^^^

``Filter(function[, event_builder])``

Value of the parameter ``function``

Possible operations on Filter instances
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

(those are, primarily logical operators)

Binary
""""""

``&`` is a logical AND for two filters
``|`` is a logical OR for two filters
``^`` is a logical XOR for two filters

Unary
"""""

``~`` is a logical NOT for a filter

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

``from garnet.filters import text``

``text.Len`` is a special class for `len(Some.raw_text ... "")` operations.
Supports logical comparison operations, such are ``==``, ``>``, ``>=``, ``<``, ``<=``

``text.startswith(prefix: str, /)`` will evaluates to ``Some.raw_text.startswith(prefix)``

``text.commands(*cmds: str, prefixes="/", to_set=True)`` will evaluate to check if command is within ``cmd`` (ignores mentions, and works on `Some.text`)

``text.match(rexpr: str, flags=0, /)`` will evaluate to ``re.compile(rexpr, flags).match(Some.raw_text)``

``text.between(*texts: str, to_set=True)`` will evaluate to ``Some.raw_text in texts``

``text.can_be_int(base=10)`` will evaluate to ``try{int(Some.raw_text);return True;}except(ValueError){return False;}``

``text.can_be_float()`` similarly to ``text.can_be_int`` but for floats.

*******************
Contacts/Community
*******************

You can find me on telegram by `@martin_winks <https://telegram.me/martin_winks>`_

Our small telegram `group <https://t.me/joinchat/B2cC_hknbKGm3_G8N9qifQ>`_


Router
=======


**********************
🤗 Credits
**********************

Finite-state machine was ported from cool BotAPI library 'aiogram', special thanks to Alex_

Support lonamiwebs: `lonamiwebs <http://paypal.me/lonamiwebs>`_

Support aiogram project: `JRootJunior <https://opencollective.com/aiogram/organization/0/website>`_
