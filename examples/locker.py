# // just an example of bitwise operators usage, locking user, not being ukrainian

from telethon import events

from garnet import TelegramClient, FSMContext, MessageText, Filter, state

bot = TelegramClient.from_env()
ATTEMPTS = 3
PASSWORD1, PASSWORD2 = "OWO", "UWU"


async def is_reached_incorrect_pass_limit(event, context: FSMContext):
    if (await context.get_data() or {}).get("attempts", 0) >= 3:
        return True
    return False


@bot.on(Filter(is_reached_incorrect_pass_limit, requires_context=True))
async def stop_propagation(*event):
    # block/kick whatever
    raise events.StopPropagation


@bot.on(~MessageText.between(PASSWORD1, PASSWORD2))
async def not_start_handler(event, context: FSMContext):
    attempts = (await context.get_data() or {}).get("attempts", 0)
    attempts += 1
    await context.update_data(attempts=attempts)
    await event.reply(f"Password incorrect. Available: {3 - attempts}")


@bot.on(MessageText.between(PASSWORD1, PASSWORD2))
async def correct_password(event, context: FSMContext):
    await event.reply("Welcome!")
    await context.set_state("onStandBy")


@bot.on(state.exact("onStandBy") & MessageText.commands("cats", prefixes="./"))
async def menu(event):
    await event.reply("Sorry, I'm not ukrainian cat-pic sender...")


@bot.on_start
async def on_start(client: TelegramClient):
    await client.start()
    await client.send_message("smn", "Bot is starting")


@bot.on_finish
async def on_finish(client: TelegramClient):
    await client.send_message("smn", "GoodBye!")


bot.run_until_disconnected()
