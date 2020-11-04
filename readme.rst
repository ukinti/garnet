
garnet
######

About
*****

garnet is a ridiculously simple library created mainly for managing your stateful telegram bots written with Telethon.

.. invisible-content
.. _aiogram: https://github.com/aiogram/aiogram



***************
How to install?
***************

Although, garnet is ``garnet``, it is named ``telegram-garnet`` on the PyPI, you'll have to tell that to pip.

``pip install telegram-garnet``


*************
Let's dive in
*************

.. code:: python

    # export BOT_TOKEN, APP_ID, APP_HASH env vars.

    from garnet import Router, events, ctx
    from garnet.filters import State, text, group
    from garnet.storages import DictStorage

    router = Router(events.NewMessage)  # declare a router that will handle message event by default
    UserStates = group.Group.from_iter(["echo"])  # declare users states

    # register handler for "/start" commands for users with none yet set state
    @router.default(text.commands("start"), State.entry)
    async def entrypoint(event):
        await event.reply("You entered echo zone!\n/cancel to exit")
        fsm = ctx.StateCtx.get()  # get UserCage of current user
        await fsm.set_state(UserStates.echo)

    # register handler for "/cancel" commands for users that have entered any state
    @router.default(text.commands("cancel"), State.any)
    async def cancel(event):
        await event.reply("Cancelled :)\n/start to restart")
        await ctx.StateCtx.get().set_state(None)

    # handle any message from users with state=UserState.echo
    @router.default(State.exact(UserState.echo))
    async def echo(event):
        await event.reply(event)

    if __name__ == "__main__":
        import asyncio
        from garnet import run
        asyncio.run(run(router, DictStorage()))


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


State filters
^^^^^^^^^^^^^

Operations on users' states.

Import
""""""

``from garnet.filters import State``

Little journey
""""""""""""""

- ``State.any`` will evaluate to match any state but not ``None``
- ``State.entry`` will evaluate to ``True`` if only current state is ``None``
- ``State.exact(state: GroupT | M | "*")`` when "*" is passed will use ``State.any``, when states group is passed will check if current state is any states from the group, when state group member (``M``) passed will check if current state is exactly this state
- ``State == {some}`` will call ``State.exact(state=some)``

Note
""""

State filter has effect on ``garnet.ctx.MCtx``.
And if you're not sure what are you doing try not to apply logical operators on ``State`` filters.
Simply, don't do ``~State.any`` or ``~State.exact(...some...)``


States declaration
^^^^^^^^^^^^^^^^^^

Import
""""""

``from garnet.filters import group``

group.M (state group Member)
""""""""""""""""""""""""""""

*yes, "M" stands for member.*

- ``.next`` return the next ``M`` in the group or raise ``group.NoNext`` exception
- ``.prev`` return the previous ``M`` in the group or raise ``group.NoPrev`` exception
- ``.top`` return the top (head) ``M`` in the group or raise ``group.NoTop`` exception

group.Group
"""""""""""

Group of state members declared as a class (can be nested)

- ``.first`` returns (``M``) the first declared member
- ``.last`` returns (``M``) the last declared member

**Note**
``.first`` and ``.last`` are reserved "keywords" for state

Usage
"""""

.. code:: python

    from garnet.filters import group, State

    class Users(group.Group):
        ask_name = group.M()
        ask_age = group.M()

        class Pet(group.Group):
            ask_name = group.M()
            ask_age = group.M()

        class Hobby(group.Group):
            frequency = group.M()
            ask_if_popular = group.M()

    # 💫 just imagine we already have router 💫

    @router.default(State.exact(Users))  # will handle all states in "Users"
    # --- some code ---
    @router.default(State.exact(Users.Pet.ask_age))  # will handle only if current state is equal to "Users.Pet.ask_age"
    # --- some code ---


Note
""""

Think of groups as an immutable(not really...) linked list of connected group members
As you can see in the example above we use nested states groups.
One thing about about ``M.[next/prev/top]``.
We can go to ``Users.Pet.ask_name`` from ``Users.ask_age`` using ``Users.ask_age.next``,
but not backwards as someone could expect with ``Users.Pet.ask_name.prev`` (will actually raise ``NoPrev``)
Nested group members do not know anything about upper members, but they have "owners" which have access to their parent groups and
in order to access parent of owner of ``x = Users.Pet.ask_name``, we would use ``x.owner``

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

- ``.on(event_builder, /, *filters)`` pass any event builder (preferably from ``garnet.events::*``)

- ``.use()`` use this decorator for intermediates that are called after filters

etc.
^^^^

- ``.add_use(intermediate, /)`` register an intermediate which will be called after filters for handlers
- ``.register(handler, filters, event_builder)`` register handler with binding filters and event_builder to it.
- ``.include(router, /)`` "include" passed router in the callee as its child router


Examples
--------

Simple cases
^^^^^^^^^^^^

.. code:: python

    from garnet import Router, events, Filter

    router = Router(events.NewMessage, Filter(lambda _: True), Filter(lambda _: True))

    @router.default(Filter(lambda _: True))
    async def handler(_): pass

Nested routers and a little intermediate
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code:: python

    from my_project.routers import public_router, admin_router
    from my_project.logging import put_event

    from garnet import Router, events

    common_router = Router().include(public_router).include(admin_router)

    @common_router.use()
    async def intermediate(handler, event):
        await put_event(event, nowait=True)
        await handler(event)


Context variables
=================

Users states
------------

``from garnet.ctx import StateCtx, MCtx``

``MCtx`` is context variable that points to the current states group member (use it carefully)
it's set in ``State`` filters


``StateCtx`` points to ``garnet.event::UserCage``


User and chat IDs
-----------------

``from garnet.ctx import UserIDCtx, ChatIDCtx``

Those will be set after router filters and before handler filters and handlers calls.

Handler
-------

``from garnet.ctx import HandlerCtx``

``HandlerCtx`` points to currently executing handler.

Note
----

Usual contextual variables, with ``.get()``, ``.set()``, ``.reset()`` methods. You'll always end up using ``.get()``.
Work with those only in handlers or handler filters.

Also every event builder in ``garnet.events`` is "contextfull", but for ``get``, ``set``, ``reset`` you shall add ``_current``
postfix.

Try to use context variables everywhere not depending on other mechanisms, because they work as you want.

*******************
Contacts/Community
*******************

You can find me on telegram by `@martin_winks <https://telegram.me/martin_winks>`_

Our small telegram `group <https://t.me/joinchat/B2cC_hknbKGm3_G8N9qifQ>`_
