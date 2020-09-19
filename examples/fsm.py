from telethon import custom, events

from garnet import TelegramClient, Router, StateCtx
from garnet.filters import State, text


POSSIBLE_PETS = ("Doggggee |}", "Cat >.<", "Human <|", "Goose 8D")
PETS = tuple([
    (custom.Button.text(_petty, resize=True),)
    for _petty in POSSIBLE_PETS
])


class States:
    name = "name"
    age = "age"
    pet = "pet"


router = Router(default_event=events.NewMessage)


@router.message(text.commands("start"))
async def handler(update: custom.Message):
    await update.reply("Hello, please enter your name!")
    await StateCtx.get().set_state(States.name)


# // handle all /cancel's from any state if only state is not None
@router.message(text.commands("cancel"), State == any)
async def cancel_handler(update: custom.Message):
    await update.reply("Ok. Resetting!")
    await StateCtx.get().reset_state(with_data=True)


@router.message(State == States.name)
async def name_handler(update: custom.Message):
    await StateCtx.get().set_data({"name": update.raw_text})
    await update.reply(
        f"{update.raw_text}, please enter your age:",
        buttons=custom.Button.force_reply(),
    )
    await StateCtx.get().set_state(States.age)


# if we can use one Filter, then let's create filter which will be cached by garnet. Optimizations 8>
ageStateFilter = State.exact(States.age)


@router.message(ageStateFilter & text.isdigit())
async def age_correct_handler(update: custom.Message):
    await StateCtx.get().update_data(age=int(update.raw_text))
    await update.reply("Cool! Now please select your favourite pet:", buttons=PETS)
    await StateCtx.get().set_state(States.pet)


@router.message(ageStateFilter & ~text.isdigit())
async def age_incorrect_handler(update: custom.Message):
    await update.reply("Please try again! Age must be digit :D")


@router.message(State.exact(States.pet) & text.between(*POSSIBLE_PETS))
async def pet_correct_handler(update: custom.Message):
    await StateCtx.get().update_data(pet=update.raw_text)
    data = await StateCtx.get().get_data()
    await update.reply(
        f"Your age: {data['age']}\n"
        f"Name: {data['name']}\n"
        f"Favourite pert: {data['pet']}\n"
        f"Thank you! To participate again send /start",
        buttons=custom.Button.clear(),
    )
    await StateCtx.get().reset_state(with_data=True)


if __name__ == '__main__':
    import asyncio
    from garnet import EventDispatcher, Runner
    from garnet.storages import MemoryStorage

    bot = TelegramClient(
        session="change me",
        api_id="change me",
        api_hash="change me"
    )
    dispatcher = EventDispatcher(MemoryStorage(), [router])
    asyncio.run(Runner(dispatcher, bot, True).run_blocking())
