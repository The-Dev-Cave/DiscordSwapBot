import lightbulb
import hikari
from BotCode.environment.database import get_database_connection
from BotCode.functions.send_logs import send_mod_log

guild_settings_plugin = lightbulb.Plugin("Commands for initializing bot messages")


@lightbulb.Check
async def user_have_mod_role(context: lightbulb.Context) -> bool:
    conn = await get_database_connection()
    role_id = await conn.fetchval(
        "select mod_role_id from guilds where guild_id=$1", context.guild_id
    )
    roles = context.member.role_ids
    return roles.__contains__(role_id)


@guild_settings_plugin.command()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.command("set", "change the settings for SwapBot", ephemeral=True)
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def guild_set():
    pass


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option("days", "1 to 31", type=int, min_value=1, max_value=31, required=True)
@lightbulb.command(
    "expiry", "days it takes for a post to expire", ephemeral=True
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def expiry(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    days = ctx.options.days

    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set expiry_time=$1 where guild_id=$2", days, guild_id
    )
    await conn.close()
    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Post Expiry** to **{days}** day(s)",
    )
    await ctx.respond(
        content=f"Set post expiry time to **{days}** days",
        flags=hikari.MessageFlag.EPHEMERAL,
    )


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option("bool", "True or False", type=bool, required=True)
@lightbulb.command(
    "post-approval",
    "Do posts need to be approved by mods before everyone can see it",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def post_approval(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    option = ctx.options.bool

    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set post_approval=$1 where guild_id=$2", option, guild_id
    )
    await conn.close()

    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Post Approval** to **{option}**",
    )
    await ctx.respond(
        content=f"Set post approval to **{option}**", flags=hikari.MessageFlag.EPHEMERAL
    )


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option("bool", "True or False", type=bool, required=True)
@lightbulb.command(
    "profile-enabled",
    "Is viewing the profile of another user allowed. Profiles are a name, pronouns, and ratings",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def profile_enabled(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    option = ctx.options.bool

    conn = await get_database_connection()
    if not option:
        await conn.execute(
            "UPDATE guilds set profile_required=FALSE, profile_enabled=$1 where guild_id=$2",
            option,
            guild_id,
        )
        await ctx.respond(
            content=f"Set profile required and profile_enabled to {option}",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        await send_mod_log(
            guild_id=guild_id,
            text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Profile Enabled ** to **{option}** which set **Profile Required** to **False** if it was enabled",
        )
        await ctx.respond(
            content=f"Set profile enabled to **{option}** which set **Profile Required** to **False** if it was enabled",
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    else:
        await conn.execute(
            "UPDATE guilds set profile_enabled=$1 where guild_id=$2", option, guild_id
        )
        await ctx.respond(
            content=f"Set profile enabled to **{option}**",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        await send_mod_log(
            guild_id=guild_id,
            text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Profile Enabled** to **{option}**",
        )
        await ctx.respond(
            content=f"Set profile enabled to **{option}**.  If you want to require profiles do </set profile-required:1066868724008755251> and set it to **True**",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
    await conn.close()


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option("bool", "True or False", type=bool, required=True)
@lightbulb.command(
    "profile-required",
    "Do people need a profile to to make and interact with posts",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def profile_required(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    option = ctx.options.bool

    conn = await get_database_connection()
    if option:
        await conn.execute(
            "UPDATE guilds set profile_required=$1, profile_enabled=TRUE where guild_id=$2",
            option,
            guild_id,
        )
        await send_mod_log(
            guild_id=guild_id,
            text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Profile Required** to **{option}** which set **Profile Required** to **True** if it was disabled",
        )
        await ctx.respond(
            content=f"Set profile required and profile_enabled to {option}",
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    else:
        await conn.execute(
            "UPDATE guilds set profile_required=$1 where guild_id=$2", option, guild_id
        )
        await send_mod_log(
            guild_id=guild_id,
            text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Profile Required** to **{option}**",
        )
        await ctx.respond(
            content=f"Set profile required to {option}",
            flags=hikari.MessageFlag.EPHEMERAL,
        )

    await conn.close()


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option("bool", "True or False", type=bool, required=True)
@lightbulb.command(
    "ratings-enabled",
    "Can people see other's ratings and rate each other after making a transaction with someone",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def ratings_enabled(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    option = ctx.options.bool

    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set ratings_enabled=$1 where guild_id=$2", option, guild_id
    )
    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Ratings Enabled** to **{option}**",
    )
    await ctx.respond(
        content=f"Set ratings enabled to {option}", flags=hikari.MessageFlag.EPHEMERAL
    )

    await conn.close()


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option(
    "times",
    "0 to 10 times or -1 for unlimited",
    type=int,
    min_value=-1,
    max_value=10,
    required=True,
)
@lightbulb.command(
    "renew",
    "How many times a user can renew a post without needing to remake",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def renew_count(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    times = ctx.options.times

    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set renewal_count=$1 where guild_id=$2", times, guild_id
    )
    await conn.close()

    if times == -1:
        await send_mod_log(
            guild_id=guild_id,
            text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Renew Amount** to **UNLIMITED**",
        )
        await ctx.respond(
            content=f"Set post renewal amount to unlimited times",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
    else:
        await send_mod_log(
            guild_id=guild_id,
            text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Profile Enabled** to **{times}**",
        )
        await ctx.respond(
            content=f"Set post renewal amount to {times} time(s)",
            flags=hikari.MessageFlag.EPHEMERAL,
        )


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option(
    "channel", "the channel", type=hikari.TextableGuildChannel, required=True
)
@lightbulb.command(
    "buy-posts-chnl",
    "The text channel that buy listings are posted",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def buy_channel(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    channel = ctx.options.channel

    if channel and (channel.type.__str__() != "GUILD_TEXT"):
        await ctx.respond(
            "Not a valid text channel", flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set buy_channel_id=$1 where guild_id=$2", channel.id, guild_id
    )
    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Buy Post Channel** to <#{channel.id}>",
    )
    await ctx.respond(
        content=f"Set **Buy Post Channel** to <#{channel.id}>",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    await conn.close()


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option(
    "channel", "the channel", type=hikari.TextableGuildChannel, required=True
)
@lightbulb.command(
    "sell-posts-chnl",
    "The text channel that sell listings are posted",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def sell_channel(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    channel = ctx.options.channel

    if channel and (channel.type.__str__() != "GUILD_TEXT"):
        await ctx.respond(
            "Not a valid text channel", flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set sell_channel_id=$1 where guild_id=$2", channel.id, guild_id
    )
    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Sell Post Channel** to <#{channel.id}>",
    )
    await ctx.respond(
        content=f"Set **Sell Post Channel** to <#{channel.id}>",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    await conn.close()


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option(
    "channel", "the channel", type=hikari.TextableGuildChannel, required=True
)
@lightbulb.command(
    "post-approval-chnl",
    "The text channel that approval of listings is done",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def approval_channel(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    channel = ctx.options.channel

    if channel and (channel.type.__str__() != "GUILD_TEXT"):
        await ctx.respond(
            "Not a valid text channel", flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set approval_channel_id=$1 where guild_id=$2",
        channel.id,
        guild_id,
    )
    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Post Approval Channel** to <#{channel.id}>",
    )
    await ctx.respond(
        content=f"Set **Post Approval Channel** to <#{channel.id}>",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    await conn.close()


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option(
    "channel", "the channel", type=hikari.TextableGuildChannel, required=True
)
@lightbulb.command(
    "public-logs-chnl",
    "The text channel for public logs to go",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def pub_logs_chnl(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    channel = ctx.options.channel

    if channel and (channel.type.__str__() != "GUILD_TEXT"):
        await ctx.respond(
            "Not a valid text channel", flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set logs_channel_id=$1 where guild_id=$2", channel.id, guild_id
    )
    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Public Logs Channel** to <#{channel.id}>",
    )
    await ctx.respond(
        content=f"Set **Public Logs Channel** to <#{channel.id}>",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    await conn.close()


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option(
    "channel", "the channel", type=hikari.TextableGuildChannel, required=True
)
@lightbulb.command(
    "mod-logs-chnl",
    "The text channel for mod logs to go",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def mod_logs_chnl(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    channel = ctx.options.channel

    if channel and (channel.type.__str__() != "GUILD_TEXT"):
        await ctx.respond(
            "Not a valid text channel", flags=hikari.MessageFlag.EPHEMERAL
        )
        return
    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set mod_log_channel_id=$1 where guild_id=$2",
        channel.id,
        guild_id,
    )
    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Mod Logs Channel** to <#{channel.id}>",
    )
    await ctx.respond(
        content=f"Set **Mod Logs Channel** to <#{channel.id}>",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    await conn.close()


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option("role", "the role", type=hikari.Role, required=True)
@lightbulb.command(
    "mod-role",
    "The role that can interact with SwapBot for moderator actions",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def mod_role(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    role = ctx.options.role

    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set mod_role_id=$1 where guild_id=$2", role.id, guild_id
    )
    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **Mod Role** to <@&{role.id}>",
    )
    await ctx.respond(
        content=f"Set **Mod Role** to <@&{role.id}>", flags=hikari.MessageFlag.EPHEMERAL
    )
    await conn.close()


@guild_set.child()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.option(
    "category", "the category", type=hikari.TextableGuildChannel, required=True
)
@lightbulb.command(
    "user-bridge-cat",
    "Category where channels between users are made",
    ephemeral=True,
)
@lightbulb.implements(lightbulb.SlashSubCommand)
async def usr_brdg_cat(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    guild_id = ctx.guild_id
    category: hikari.TextableGuildChannel = ctx.options.category
    if category and (category.type.__str__() != "GUILD_CATEGORY"):
        await ctx.respond("Not a guild category", flags=hikari.MessageFlag.EPHEMERAL)
        return
    conn = await get_database_connection()
    await conn.execute(
        "UPDATE guilds set user_bridge_cat_id=$1 where guild_id=$2",
        category.id,
        guild_id,
    )
    await send_mod_log(
        guild_id=guild_id,
        text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has changed **User Bridge Category** to <#{category.id}>",
    )
    await ctx.respond(
        content=f"Set **User Bridge Category** to <#{category.id}>",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    await conn.close()


# @guild_set.child()
# @lightbulb.add_checks(user_have_mod_role)
# @lightbulb.app_command_permissions(
#     perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
# )
# @lightbulb.option(
#     "minutes",
#     "0 to 1440 minutes up to one day",
#     type=int,
#     min_value=0,
#     max_value=1440,
#     required=True,
# )
# @lightbulb.command(
#     "listing-delay",
#     "Minutes between making posts. 0 for no delay, 1440 for 1 day",
#     ephemeral=True,
# )
# @lightbulb.implements(lightbulb.SlashSubCommand)
# async def listing_delay(ctx: lightbulb.SlashContext):
#     await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
#     guild_id = ctx.guild_id
#     times = ctx.options.times
#
#     conn = await get_database_connection()
#     await conn.execute(
#         "UPDATE guilds set renewal_count=$1 where guild_id=$2", times, guild_id
#     )
#     await conn.close()
#
#     if times == -1:
#         await ctx.respond(
#             content=f"Set post renewal amount to unlimited times",
#             flags=hikari.MessageFlag.EPHEMERAL,
#         )
#     else:
#         await ctx.respond(
#             content=f"Set post renewal amount to {times} time(s)",
#             flags=hikari.MessageFlag.EPHEMERAL,
#         )


@guild_settings_plugin.command()
@lightbulb.add_checks(user_have_mod_role)
@lightbulb.app_command_permissions(
    perms=hikari.Permissions.ADMINISTRATOR, dm_enabled=False
)
@lightbulb.command("settings", "view and change settings for SwapBot")
@lightbulb.implements(lightbulb.SlashCommand)
async def guild_settings(ctx: lightbulb.SlashContext):
    await ctx.respond(hikari.ResponseType.DEFERRED_MESSAGE_CREATE, flags=hikari.MessageFlag.EPHEMERAL)
    bot_name = (
        await ctx.bot.rest.fetch_member(ctx.guild_id, ctx.bot.get_me().id)
    ).display_name
    conn = await get_database_connection()
    guild_settings_row = await conn.fetchrow(
        "SELECT guild_id, buy_channel_id, sell_channel_id, approval_channel_id, user_bridge_cat_id, logs_channel_id, mod_log_channel_id, mod_role_id, post_approval, profile_approval, profile_required, profile_enabled, ratings_enabled, listing_delay, expiry_time, renewal_count from guilds where guild_id=$1",
        ctx.guild_id,
    )
    await conn.close()
    embed = hikari.Embed(
        title=f"{bot_name} Settings",
        description=f"The following are the current settings for {bot_name}.  Use `/set (setting) (option)` to change the settings",
    )
    embed.color = 0xFFDD00

    cat = await ctx.bot.rest.fetch_channel(guild_settings_row.get("user_bridge_cat_id"))
    sell_chnl = await ctx.bot.rest.fetch_channel(
        guild_settings_row.get("sell_channel_id")
    )
    buy_chnl = await ctx.bot.rest.fetch_channel(
        guild_settings_row.get("buy_channel_id")
    )

    embed.add_field(
        f"Post Approval = {guild_settings_row.get('post_approval')}",
        "Do moderators need to approv`e posts before everyone can see and interact with them. \n</set post-approval:1066868724008755251> \n**Default: True**",
        inline=True,
    )
    embed.add_field(
        f"Profile Enabled = {guild_settings_row.get('profile_enabled')}",
        "Is viewing the profile of another user allowed. Profiles are a name, pronouns, and ratings. \n</set profile-enabled:1066868724008755251> \n**Default: True**",
        inline=True,
    )
    embed.add_field(
        f"Profile Required = {guild_settings_row.get('profile_required')}",
        "Do people need a profile to to make and interact with posts. \n</set profile-required:1066868724008755251> \n**Default: False**",
        inline=True,
    )
    embed.add_field(
        f"Ratings Enabled = {guild_settings_row.get('ratings_enabled')}",
        "Can people see other's ratings and can they rate each other after making a transaction with someone. Ratings are global \n</set ratings-enabled:1066868724008755251>\n**Default: True**",
        inline=True,
    )
    # embed.add_field(
    #     f"Listing Delay = {guild_settings_row.get('listing_delay')} Minutes",
    #     "How many minutes between making posts. \n</set listing-delay:1066868724008755251>\n**Default: 0**",
    #     inline=True,
    # )
    embed.add_field(
        f"Post Expiry = {guild_settings_row.get('expiry_time')} Days",
        "How many days it takes a post to expire. \n</set expiry:1066868724008755251> \n**Default: 7**",
        inline=True,
    )
    embed.add_field(
        f"Post Renewal = {guild_settings_row.get('renewal_count')} Days",
        "How many times someone can repost without needing to remake it. \n</set renew:1066868724008755251> \n**Default: 3**",
        inline=True,
    )
    embed.add_field(
        f"Mod Role",
        f"<@&{guild_settings_row.get('mod_role_id')}>\n</set mod-role:1066868724008755251>",
        inline=True,
    )
    embed.add_field(
        f"Channels",
        "The channels set for this guild and how to change them",
        inline=False,
    )
    embed.add_field(
        f"User Bridge Category = {cat.name}",
        "</set user-bridge-cat:1066868724008755251>",
        inline=True,
    )
    embed.add_field(
        f"Postings Channels",
        f"Sell - {sell_chnl.mention}\n</set sell-posts-chnl:1066868724008755251>\n\nBuy - {buy_chnl.mention}\n</set buy-posts-chnl:1066868724008755251>",
        inline=True,
    )
    embed.add_field(
        f"Post Approval Channel",
        f"<#{guild_settings_row.get('approval_channel_id')}>\n\n</set post-approval-chnl:1066868724008755251>",
        inline=True,
    )
    embed.add_field(
        f"Logs",
        f"Public = <#{guild_settings_row.get('logs_channel_id')}>\n</set public-logs-chnl:1066868724008755251>\n\nPublic = <#{guild_settings_row.get('mod_log_channel_id')}>\n</set mod-logs-chnl:1066868724008755251>",
        inline=True,
    )

    await ctx.respond(embed=embed, flags=hikari.MessageFlag.EPHEMERAL)


@guild_settings.set_error_handler()
@guild_set.set_error_handler()
async def mod_role_error_handler(event: lightbulb.CommandErrorEvent) -> bool:
    await event.context.respond(
        f"Must have the role set as the mod role {event.bot.get_me().mention} and have administrator to run this command",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    return True


def load(bot: lightbulb.BotApp):
    bot.add_plugin(guild_settings_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(guild_settings_plugin)
