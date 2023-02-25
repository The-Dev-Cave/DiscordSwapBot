import hikari
import lightbulb

from BotCode.environment.database import get_database_connection

logs_plugin = lightbulb.Plugin("Guild Logs")


async def send_public_log(guild_id: int | hikari.Snowflake, text: str) -> None:
    conn = await get_database_connection()
    channel = await conn.fetchval(
        "Select logs_channel_id from guilds where guild_id=$1", guild_id
    )
    await conn.close()
    await logs_plugin.bot.rest.create_message(channel=channel, content=text)


async def send_mod_log(guild_id: int | hikari.Snowflake, text: str) -> None:
    conn = await get_database_connection()
    channel = await conn.fetchval(
        "Select mod_log_channel_id from guilds where guild_id=$1", guild_id
    )
    await conn.close()
    await logs_plugin.bot.rest.create_message(channel=channel, content=text)


def load(bot):
    bot.add_plugin(logs_plugin)


def unload(bot):
    bot.remove_plugin(logs_plugin)
