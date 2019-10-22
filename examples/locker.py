# // just an example of bitwise operators usage, locking user
# // Context magic usage included.

from garnet import (
    TelegramClient,
    FSMContext,
    MessageText,
    Filter,
    state,
    events,
)

from garnet.functions import messages

bot = TelegramClient.from_env()
ATTEMPTS = 3
PASSWORD1, PASSWORD2 = "OWO", "UWU"


async def reached_incorrect_pass_limit(event, context: FSMContext) -> bool:
    return (await context.get_data() or {}).get("attempts", 0) >= 3


@bot.on(Filter(reached_incorrect_pass_limit, requires_context=True))
async def stop_propagation(*_):
    # block/kick whatever
    raise events.StopPropagation  # call StopPropagation as Handler registered first and blocking


@bot.on(~MessageText.between(PASSWORD1, PASSWORD2))
async def not_start_handler(_, context: FSMContext):
    attempts = (await context.get_data() or {}).get("attempts", 0)
    attempts += 1
    await context.update_data(attempts=attempts)
    await messages.reply(
        f"Password incorrect. Available: {3 - attempts}"
    )  # you can use contextvars magic here


@bot.on(MessageText.between(PASSWORD1, PASSWORD2))
async def correct_password(_, context: FSMContext):
    await messages.reply("Welcome!")
    await context.set_state("onStandBy")


@bot.on(state.exact("onStandBy") & MessageText.commands("cats", prefixes="./"))
async def menu(_):
    await messages.reply("Sorry, I'm not ukrainian cat-pic sender...")


@bot.on_start
async def on_start(client: TelegramClient):
    await client.start()
    await client.send_message("smn", "Bot is starting")


@bot.on_finish
async def on_finish(client: TelegramClient):
    await client.send_message("smn", "GoodBye!")


bot.run_until_disconnected()
