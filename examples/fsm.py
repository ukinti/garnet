from telethon import custom

from garnet import TelegramClient, FSMContext, MessageText, CurrentState


# // genders in parallel universe buttons
buttons = (
    (custom.Button.text("Abuser", resize=True),),
    (custom.Button.text("Dishwasher"),),
    (custom.Button.text("Cat"),),
)


# /*
#  * get configurations from environment variable
#  * look garnet.TelegramClient::Env for more
#  */
bot = TelegramClient.from_env()


@bot.on(MessageText.commands("start"))
async def handler(update: custom.Message, context: FSMContext):
    await update.reply(f"Hello, please enter your name!")
    await context.set_state("stateName")


# // handle all /cancel's from any state if only state is not None
@bot.on(MessageText.commands("cancel"), CurrentState == any)
async def cancel_handler(update: custom.Message, context: FSMContext):
    await update.reply("Ok. Resetting!")
    await context.reset_state(with_data=True)


@bot.on(CurrentState == "stateName")
async def name_handler(update: custom.Message, context: FSMContext):
    await context.set_data({"name": update.raw_text})
    await update.reply(
        f"{update.raw_text}, please enter your age:",
        buttons=custom.Button.force_reply(),
    )
    await context.set_state("stateAge")


# if we can use one Filter, then let's create filter which will be cached by garnet. Optimizations 8>
ageStateFilter = CurrentState.exact("stateAge")


@bot.on(ageStateFilter & MessageText.isdigit())
async def age_correct_handler(update: custom.Message, context: FSMContext):
    await context.update_data(age=int(update.raw_text))
    await update.reply(f"Cool! Now please select your gender:", buttons=buttons)
    await context.set_state("stateGender")


@bot.on(ageStateFilter & ~MessageText.isdigit())
async def age_incorrect_handler(update: custom.Message):
    await update.reply(f"Please try again! Age must be digit :D")


@bot.on(CurrentState.exact("stateGender") & MessageText.between("Abuser", "Dishwasher", "Cat"))
async def gender_correct_handler(update: custom.Message, context: FSMContext):
    await context.update_data(gender=update.raw_text)
    data = await context.get_data()
    await update.reply(
        f"Your age: {data['age']}\n"
        f"Name: {data['name']}\n"
        f"Gender: {data['gender']}\n"
        f"Thank you! You can participate again!",
        buttons=custom.Button.clear(),
    )
    await context.reset_state(with_data=True)


if __name__ == '__main__':
    @bot.on_start
    async def main(_):
        await bot.start_as_bot()


    bot.run_until_disconnected()
