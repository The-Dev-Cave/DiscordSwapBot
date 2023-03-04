import asyncio
import os

import flare
import hikari
import lightbulb
from lightbulb.ext import tasks
from dotenv import load_dotenv

bot_root_directory = f"{os.getcwd()}"


async def create_bot() -> lightbulb.BotApp:
    load_dotenv()
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    bot = lightbulb.BotApp(
        token=BOT_TOKEN,
        intents=hikari.Intents.ALL_UNPRIVILEGED,
        help_class=None,
    )

    @bot.command()
    @lightbulb.command("reload", "reload plugins")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def _foo(ctx: lightbulb.SlashContext) -> None:
        ctx.bot.reload_extensions(*ctx.bot.extensions)
        await ctx.respond("Done", flags=hikari.MessageFlag.EPHEMERAL)

    flare.install(bot)
    tasks.load(bot)

    bot.load_extensions_from("./BotCode/environment", recursive=True)
    bot.load_extensions_from("./BotCode/listeners", recursive=True)
    bot.load_extensions_from("./BotCode/commands", recursive=True)
    bot.load_extensions_from("./BotCode/functions", recursive=True)
    bot.load_extensions_from("./BotCode/interactions", recursive=True)
    bot.load_extensions_from("./BotCode/tasks", recursive=True)

    return bot
