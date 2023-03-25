import hikari
import lightbulb
from BotCode.environment.database import get_database_connection

help_cmd_plugin = lightbulb.Plugin("Commands for initializing bot messages")


@help_cmd_plugin.command()
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command("help", "Get basic info how to use the bot", ephemeral=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def help_pub(ctx: lightbulb.SlashContext):
    await ctx.respond(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL
    )
    # conn = await get_database_connection()
    # row = await conn.fetchrow("SELECT * from guilds where guild_id=$1", ctx.guild_id)
    # await conn.close()
    bot_id = ctx.bot.get_me().id
    HELP_MESSAGE = f"""
    How To Make A Post:
     - Have DMs allowed from the server so <@{bot_id}> can DM you to make your post
     - You can also go to `https://swapbot.thedevcave.xyz`
     - Go to the designated channel for making a post and select which post type you want to make
     - Follow prompts from the bot to create the post
    """
    await ctx.respond(HELP_MESSAGE)


@help_cmd_plugin.command()
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.command("admin-help", "Help for admins", ephemeral=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def help_admin(ctx: lightbulb.SlashContext):
    await ctx.respond(
        hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL
    )
    conn = await get_database_connection()
    row = await conn.fetchrow("SELECT * from guilds where guild_id=$1", ctx.guild_id)
    await conn.close()
    bot_id = ctx.bot.get_me().id
    HELP_MESSAGE = f"""
    How To Initialize The Bot:
     - Run </initialize:1063552012593156106> to create the designated channels and set the bot moderator role
        - moderator-role: the role that can run commands for the bot
        - moderaator-logs: private logs for mods from <@{bot_id}>
        - public-logs: public logs for posts interactions from <@{bot_id}>
        - approval-channel: where posts go to be approved if setting enabled
     Change Bot Settings:
      - Run </settings:1066868725162180768> to see current settings and how to change
    """
    await ctx.respond(HELP_MESSAGE)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(help_cmd_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(help_cmd_plugin)
