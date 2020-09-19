from functools import partial

from telethon import custom, events
from garnet import TelegramClient, State
from garnet.filters import text, state
from garnet.events.router import Router
from garnet.helpers import var

POSSIBLE_PETS = ("Doggggee |}", "Cat >.<", "Human <|", "Goose 8D")
PETS = tuple([
    (custom.Button.text(_petty, resize=True),)
    for _petty in POSSIBLE_PETS
])


class States:
    _auto = partial(var.Var, prefix="state:")

    name: str = _auto()  # state:name
    age: str = _auto()   # state:age
    pet: str = _auto()   # state:pet


bot = TelegramClient(..., ..., ...)

router = Router(default_event=events.NewMessage)


@router.message(text.commands("start"))
async def handler(update: custom.Message):
    await update.reply(f"Hello, please enter your name!")
    await State.get().set_state(States.name)


# // handle all /cancel's from any state if only state is not None
@router.message(text.commands("cancel"), state.CurrentState == any)
async def cancel_handler(update: custom.Message):
    await update.reply("Ok. Resetting!")
    await State.get().reset_state(with_data=True)


@router.message(state.CurrentState == States.name)
async def name_handler(update: custom.Message):
    await State.get().set_data({"name": update.raw_text})
    await update.reply(
        f"{update.raw_text}, please enter your age:",
        buttons=custom.Button.force_reply(),
    )
    await State.get().set_state(States.age)


# if we can use one Filter, then let's create filter which will be cached by garnet. Optimizations 8>
ageStateFilter = state.CurrentState.exact(States.age)


@router.message(ageStateFilter & text.isdigit())
async def age_correct_handler(update: custom.Message):
    await State.get().update_data(age=int(update.raw_text))
    await update.reply(f"Cool! Now please select your favourite pet:", buttons=PETS)
    await State.get().set_state(States.pet)


@router.message(ageStateFilter & ~text.isdigit())
async def age_incorrect_handler(update: custom.Message):
    await update.reply(f"Please try again! Age must be digit :D")


@router.message(state.CurrentState.exact(States.pet) & text.between(*POSSIBLE_PETS))
async def pet_correct_handler(update: custom.Message):
    await State.get().update_data(pet=update.raw_text)
    data = await State.get().get_data()
    await update.reply(
        f"Your age: {data['age']}\n"
        f"Name: {data['name']}\n"
        f"Favourite pert: {data['pet']}\n"
        f"Thank you! To participate again send /start",
        buttons=custom.Button.clear(),
    )
    await State.get().reset_state(with_data=True)


if __name__ == '__main__':
    import asyncio
    from garnet import runner, EventDispatcher, storages

    dispatcher = EventDispatcher(storages.MemoryStorage(), [router])
    asyncio.run(runner.Runner(dispatcher, bot, True).run_blocking())

