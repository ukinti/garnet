from telethon import events, sessions

from garnet import Router, TelegramClient, run_bot, make_handle
from garnet.filters import text, State, group
from garnet import ctx
from garnet.storages import MemoryStorage

router = Router(default_event=events.NewMessage)


class States(group.Group):
    state_a = group.M()
    state_b = group.M()


@router.message(text.commands("start", prefixes=".!/") & State.entry)
async def response(event):
    await event.reply("Hi! Congrats, you're stuck now 👿")
    await ctx.StateCtx.get().set_state(States.first)


@router.message(State.exact(States))
async def for_x_states(event):
    cur_state = ctx.MCtx.get()

    await event.reply(f"You're in {cur_state!s}")
    try:
        nxt = cur_state.next
    except group.NoNext:
        nxt = cur_state.top

    await ctx.StateCtx.get().set_state(nxt)


async def main():
    bot = TelegramClient(
        sessions.StringSession(),
        api_id=0,  # todo: ChangeMe,
        api_hash="",  # todo: ChangeMe
    )

    main_router = Router().include(router)
    handle_config = make_handle([main_router], MemoryStorage())
    await run_bot(handle_config, bot)


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
