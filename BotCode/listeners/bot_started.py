import asyncio
import asyncpg
from BotCode.environment.database import create_pool, get_database_connection
import lightbulb
import hikari

lightbulb_events_plugin = lightbulb.Plugin("Lightbulb Bot Events")


@lightbulb_events_plugin.listener(event=lightbulb.LightbulbStartedEvent)
async def lightbulb_started(event: lightbulb.LightbulbStartedEvent):
    await create_pool()


def load(bot: lightbulb.BotApp):
    bot.add_plugin(lightbulb_events_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(lightbulb_events_plugin)
