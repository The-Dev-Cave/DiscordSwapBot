import flare
import lightbulb
import hikari

from BotCode.environment.database import get_database_connection
from BotCode.interactions.buttons.buttons_profile import ButtonCreateProfile
from BotCode.interactions.buttons.buttons_posts import ButtonCreatePost

init_commands_plugin = lightbulb.Plugin("Commands for initializing bot messages")


@lightbulb.Check
async def user_have_mod_role(context: lightbulb.Context) -> bool:
    conn = await get_database_connection()
    role_id = await conn.fetchval("select mod_role_id from guilds where guild_id=$1", context.guild_id)
    roles = context.member.role_ids
    return roles.__contains__(role_id)


@init_commands_plugin.command()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.command("initpost", "Initialize create posts message")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_init(ctx: lightbulb.SlashContext) -> None:
    embed = hikari.Embed(
        title="Listing Instructions",
        description="To create a listing, click the button that best aligns with what you'd like to do. I will walk you through each process respectively in DM's.\nOr you can go to swap.thedevcave.xyz and make them there",
    )
    embed.set_footer(
        "This bot is in beta, please let a moderator know if you run into any issues."
    )
    embed.color = 0xFFDD00
    buttons = await flare.Row(
        ButtonCreatePost(post_type="sell", label="I'm Looking To Sell", guild_id=ctx.guild_id),
        ButtonCreatePost(post_type="buy", label="I'm Looking To Buy", guild_id=ctx.guild_id),
    )

    await init_commands_plugin.bot.rest.create_message(
        ctx.channel_id, embed=embed, component=buttons
    )
    await ctx.respond(
        content="Init msg created successfully", flags=hikari.MessageFlag.EPHEMERAL
    )


@init_commands_plugin.command()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.command("initprofile", "Initialize Profile Message")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_intProfile(ctx: lightbulb.SlashContext):
    await ctx.respond(
        "Initialization of message completed", flags=hikari.MessageFlag.EPHEMERAL
    )
    build_embed = hikari.Embed(
        title="Build Your Profile",
        description="Click the button below to build your"
        " profile and get access to the"
        " rest of the server",
    )

    row = await flare.Row(ButtonCreateProfile(label="Build Profile"))

    await init_commands_plugin.bot.rest.create_message(
        ctx.channel_id,
        embed=build_embed,
        component=row,
    )
    return


@cmd_init.set_error_handler()
@cmd_intProfile.set_error_handler()
async def mod_role_error_handler(event: lightbulb.CommandErrorEvent) -> bool:
    await event.context.respond(f"Must have the role set as the mod role {event.bot.get_me().mention} and have administrator to run this command", flags=hikari.MessageFlag.EPHEMERAL)
    return True


def load(bot: lightbulb.BotApp):
    bot.add_plugin(init_commands_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(init_commands_plugin)
