from garnet import ctx
from garnet.filters import text, State, group
from garnet.storages import DictStorage
from garnet.events import Router

router = Router()


class States(group.Group):
    state_a = group.M()
    state_b = group.M()


@router.message(text.commands("start", prefixes=".!/") & State.entry)
async def response(event):
    await event.reply("Hi! Congrats, you're stuck now!")
    await ctx.CageCtx.get().set_state(States.first)


@router.message(State.exact(States))
async def for_x_states(event):
    cur_state = ctx.MCtx.get()

    await event.reply(f"You're in {cur_state!s}")
    try:
        nxt = cur_state.next
    except group.NoNext:
        nxt = cur_state.top

    await ctx.CageCtx.get().set_state(nxt)


async def main():
    from garnet.runner import run

    main_router = Router().include(router)
    await run(main_router, DictStorage())


if __name__ == "__main__":
    from garnet.runner import launch
    launch("circular-states-app", main(),)
