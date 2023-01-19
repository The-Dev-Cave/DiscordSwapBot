import flare
import hikari
import lightbulb
from hikari import PermissionOverwriteType, Permissions

from BotCode.environment.database import get_database_connection
from BotCode.interactions.buttons.buttons_posts import ButtonCreatePost
from BotCode.interactions.buttons.buttons_profile import ButtonCreateProfile

guild_init_plugin = lightbulb.Plugin("Commands for initializing bot messages")


@guild_init_plugin.command()
@lightbulb.app_command_permissions(perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False)
@lightbulb.option("approval-channel", "Optional: Channel for mods to approve post if post approval enabled", type=hikari.TextableGuildChannel, required=False)
@lightbulb.option("public-logs", "Optional: Log channel for all users to see post history or one will be created", type=hikari.TextableGuildChannel, required=False)
@lightbulb.option("moderator-logs", "Optional: Log channel for mods only or one will be created", type=hikari.TextableGuildChannel, required=False)
@lightbulb.option("moderator-role", "Role to use bot moderation features", type=hikari.Role, required=True)
@lightbulb.command("initialize", "Create channels and categories for bot features to work", auto_defer=True)
@lightbulb.implements(lightbulb.SlashCommand)
async def init_guild(ctx: lightbulb.SlashContext):
    conn = await get_database_connection()

    row = await conn.fetchrow(f"Select guild_id from guilds where guild_id={ctx.guild_id}")
    if row:
        await ctx.respond(f"Guild already initialized, use `/settings` to change <@{ctx.bot.get_me().id}> settings")
        await conn.close()
        return
    await conn.close()

    apprv_chnl = ctx.options.__getitem__("approval-channel")
    if apprv_chnl and (apprv_chnl.type == "GUILD_CATEGORY"):
        apprv_chnl = None

    public_logs_chnl = ctx.options.__getitem__("public-logs")
    if public_logs_chnl and (public_logs_chnl.type == "GUILD_CATEGORY"):
        public_logs_chnl = None

    mod_logs_chnl = ctx.options.__getitem__("moderator-logs")
    if mod_logs_chnl and (mod_logs_chnl.type == "GUILD_CATEGORY"):
        mod_logs_chnl = None

    mod_role: hikari.Role = ctx.options.__getitem__("moderator-role")

    embed = hikari.Embed(
        title="Listing Instructions",
        description="To create a listing, click the button that best aligns with what you'd like to do. I will walk you through each process respectively in DM's.\nOr you can go to swap.thedevcave.xyz and make them there",
    )
    embed.color = 0xFFDD00
    buttons = await flare.Row(
        ButtonCreatePost(post_type="sell", label="I'm Looking To Sell", guild_id=ctx.guild_id),
        ButtonCreatePost(post_type="buy", label="I'm Looking To Buy", guild_id=ctx.guild_id),
        # ButtonCreatePost(post_type="trading", label="I'm Looking To Trade"),
    )

    allow_bot = hikari.PermissionOverwrite(
                id=ctx.bot.get_me().id,
                type=PermissionOverwriteType.MEMBER,
                allow=(
                        Permissions.VIEW_CHANNEL
                        | Permissions.READ_MESSAGE_HISTORY
                        | Permissions.SEND_MESSAGES
                )
            )

    deny_all_everyone = hikari.PermissionOverwrite(
                id=ctx.guild_id,
                type=PermissionOverwriteType.ROLE,
                deny=(
                        Permissions.VIEW_CHANNEL
                        | Permissions.READ_MESSAGE_HISTORY
                        | Permissions.SEND_MESSAGES
                )
            )
    deny_send_everyone = hikari.PermissionOverwrite(
        id=ctx.guild_id,
        type=PermissionOverwriteType.ROLE,
        deny=(
                Permissions.SEND_MESSAGES
        )
    )
    allow_view_everyone = hikari.PermissionOverwrite(
        id=ctx.guild_id,
        type=PermissionOverwriteType.ROLE,
        allow=(
                Permissions.VIEW_CHANNEL
                | Permissions.READ_MESSAGE_HISTORY
        )
    )

    build_profile_embed = hikari.Embed(
        title="Build Your Profile",
        description="Click the button below to build your"
                    " profile and get access to the"
                    " rest of the server",
    )

    user_bridge_cat = await ctx.bot.rest.create_guild_category(ctx.guild_id, "SwapBot - User Bridge", reason="Initialize SwapBot", permission_overwrites=[deny_all_everyone, allow_bot])
    post_cat = await ctx.bot.rest.create_guild_category(ctx.guild_id, "SwapBot", reason="Initialize SwapBot")
    create_post_chnl = await ctx.bot.rest.create_guild_text_channel(ctx.guild_id, "Make-A-Post", category=post_cat, permission_overwrites=[deny_send_everyone, allow_bot, allow_view_everyone])
    btn_row = await flare.Row(ButtonCreateProfile(label="Build Profile"))
    await create_post_chnl.send(embed=build_profile_embed, component=btn_row)
    await create_post_chnl.send(embed=embed, component=buttons)
    buy_channel = await ctx.bot.rest.create_guild_text_channel(ctx.guild_id, "Looking-To-Buy", category=post_cat, permission_overwrites=[deny_send_everyone, allow_bot, allow_view_everyone])
    sell_channel = await ctx.bot.rest.create_guild_text_channel(ctx.guild_id, "Looking-To-Sell", category=post_cat, permission_overwrites=[deny_send_everyone, allow_bot, allow_view_everyone])

    if not apprv_chnl:
        overwrites = [
            hikari.PermissionOverwrite(
                id=mod_role.id,
                type=PermissionOverwriteType.ROLE,
                allow=(
                        Permissions.VIEW_CHANNEL
                        | Permissions.READ_MESSAGE_HISTORY
                        | Permissions.SEND_MESSAGES
                )
            ),
            hikari.PermissionOverwrite(
                id=ctx.guild_id,
                type=PermissionOverwriteType.ROLE,
                deny=(
                        Permissions.VIEW_CHANNEL
                        | Permissions.READ_MESSAGE_HISTORY
                        | Permissions.SEND_MESSAGES
                )
            ),
        ]
        apprv_chnl = await ctx.bot.rest.create_guild_text_channel(ctx.guild_id, "SwapBot-Approvals", category=post_cat, permission_overwrites=overwrites)

    if not mod_logs_chnl:
        overwrites = [
            hikari.PermissionOverwrite(
                id=mod_role.id,
                type=PermissionOverwriteType.ROLE,
                allow=(
                        Permissions.VIEW_CHANNEL
                        | Permissions.READ_MESSAGE_HISTORY
                        | Permissions.SEND_MESSAGES
                )
            ),
            hikari.PermissionOverwrite(
                id=ctx.guild_id,
                type=PermissionOverwriteType.ROLE,
                deny=(
                        Permissions.VIEW_CHANNEL
                        | Permissions.READ_MESSAGE_HISTORY
                        | Permissions.SEND_MESSAGES
                )
            ),
        ]
        mod_logs_chnl = await ctx.bot.rest.create_guild_text_channel(ctx.guild_id, "SwapBot-Mod-Log", category=post_cat, permission_overwrites=overwrites)

    if not public_logs_chnl:
        overwrites = [
            hikari.PermissionOverwrite(
                id=ctx.guild_id,
                type=PermissionOverwriteType.ROLE,
                allow=(
                        Permissions.VIEW_CHANNEL
                        | Permissions.READ_MESSAGE_HISTORY
                ),
                deny=(
                        Permissions.SEND_MESSAGES
                )
            ),
        ]
        public_logs_chnl = await ctx.bot.rest.create_guild_text_channel(ctx.guild_id, "SwapBot-Posts-Log", category=post_cat, permission_overwrites=overwrites)

    conn = await get_database_connection()
    await conn.execute(f"INSERT INTO guilds (guild_id, buy_channel_id, sell_channel_id, approval_channel_id, user_bridge_cat_id, logs_channel_id, mod_log_channel_id, mod_role_id) values"
                       f"({ctx.guild_id}, {buy_channel.id}, {sell_channel.id}, {apprv_chnl.id}, {user_bridge_cat.id}, {public_logs_chnl.id}, {mod_logs_chnl.id}, {mod_role.id})")
    await conn.close()
    await ctx.respond(f"<@{ctx.bot.get_me().id}> channels and categories initialized")


def load(bot: lightbulb.BotApp):
    bot.add_plugin(guild_init_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(guild_init_plugin)