from functools import partial

from telethon import custom, events
from garnet import TelegramClient, FSMContext, MessageText, CurrentState
from garnet.router import Router
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


# /*
#  * get configurations from environment variable
#  * look garnet.TelegramClient::Env for more
#  */
bot = TelegramClient.from_env()

router = Router(event=events.NewMessage())


@router.on(MessageText.commands("start"))
async def handler(update: custom.Message, context: FSMContext):
    await update.reply(f"Hello, please enter your name!")
    await context.set_state(States.name)


# // handle all /cancel's from any state if only state is not None
@router.on(MessageText.commands("cancel"), CurrentState == any)
async def cancel_handler(update: custom.Message, context: FSMContext):
    await update.reply("Ok. Resetting!")
    await context.reset_state(with_data=True)


@router.on(CurrentState == States.name)
async def name_handler(update: custom.Message, context: FSMContext):
    await context.set_data({"name": update.raw_text})
    await update.reply(
        f"{update.raw_text}, please enter your age:",
        buttons=custom.Button.force_reply(),
    )
    await context.set_state(States.age)


# if we can use one Filter, then let's create filter which will be cached by garnet. Optimizations 8>
ageStateFilter = CurrentState.exact(States.age)


@router.on(ageStateFilter & MessageText.isdigit())
async def age_correct_handler(update: custom.Message, context: FSMContext):
    await context.update_data(age=int(update.raw_text))
    await update.reply(f"Cool! Now please select your favourite pet:", buttons=PETS)
    await context.set_state(States.pet)


@router.on(ageStateFilter & ~MessageText.isdigit())
async def age_incorrect_handler(update: custom.Message):
    await update.reply(f"Please try again! Age must be digit :D")


@router.on(CurrentState.exact(States.pet) & MessageText.between(*POSSIBLE_PETS))
async def pet_correct_handler(update: custom.Message, context: FSMContext):
    await context.update_data(pet=update.raw_text)
    data = await context.get_data()
    await update.reply(
        f"Your age: {data['age']}\n"
        f"Name: {data['name']}\n"
        f"Favourite pert: {data['pet']}\n"
        f"Thank you! To participate again send /start",
        buttons=custom.Button.clear(),
    )
    await context.reset_state(with_data=True)


if __name__ == '__main__':
    @bot.on_start
    async def main(_):
        bot.bind_routers(router)
        await bot.start_as_bot()


    bot.run_until_disconnected()
