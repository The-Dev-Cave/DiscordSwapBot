import asyncio

import flare
import lightbulb
import hikari

from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import create_profile_embed
from BotCode.interactions.buttons.buttons_profile_edit import ButtonApproveChange, ButtonDenyChange

profile_edit_pl = lightbulb.Plugin("statusUpdater")


# OPTIONAL: Converting the check function into a Check object
@lightbulb.Check
# Defining the custom check function
async def check_author_has_profile(context: lightbulb.Context) -> bool:
    user = context.author
    conn = await get_database_connection()

    row = await conn.fetchrow(
        f"select first_name, last_name from profiles where user_id={user.id} and stage=7"
    )

    if row is None:
        return False
    else:
        return True


@profile_edit_pl.command()
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command("profile", "profiles commands")
@lightbulb.implements(lightbulb.SlashCommandGroup)
async def profile():
    return


@profile.child()
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.command("edit", "edit your profile or listings")
@lightbulb.implements(lightbulb.SlashSubGroup)
async def edit():
    return


@edit.child()
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(check_author_has_profile)
@lightbulb.option("name", "What to change your first name to", required=True)
@lightbulb.command("firstname", "edit your first name")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def f_name(ctx: lightbulb.SlashContext):
    conn = await get_database_connection()

    new_name = ctx.options.name

    await conn.execute(
        f"UPDATE profiles SET first_name = '{new_name.title()}' where user_id = {ctx.user.id}"
    )
    await ctx.bot.rest.edit_member(guild=ctx.guild_id, user=ctx.user,
                                   nickname=f'{new_name} {ctx.member.display_name.split(" ")[1]}')
    await ctx.respond(
        content=f"First name changed to: {new_name.title()}",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    await conn.close()


@edit.child()
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(check_author_has_profile)
@lightbulb.option(
    "proof",
    "Any document that shows your new last name like a school id for example",
    type=hikari.Attachment,
    required=True,
)
@lightbulb.option("name", "What to change your last name to", required=True)
@lightbulb.command("lastname", "edit your last name")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def l_name(ctx: lightbulb.SlashContext):
    new_name = ctx.options.name.title()
    proof = ctx.options.proof
    proof: hikari.Attachment
    if "image" not in proof.media_type:
        await ctx.respond(
            content=f"An image file that discord recognizes was not attached",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    await ctx.respond(
        content=f"Last name will be changed to `{new_name}` with admin approval",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    btns = await flare.Row(ButtonApproveChange(prof_id=ctx.user.id, change_type="lname", change_to=new_name),
                           ButtonDenyChange(prof_id=ctx.user.id))

    embed = hikari.Embed(
        title="Lastname Name Change",
        description=f"User: {ctx.user.mention} has requested to have their lastname changed to {new_name}",
    )
    embed.set_image(proof)
    conn = await get_database_connection()
    approve_chnl_id = await conn.fetchval(f"Select approval_channel_id from guilds where guild_id={ctx.guild_id}")
    await ctx.bot.rest.create_message(
        channel=approve_chnl_id, embed=embed, components=[btns]
    )
    await conn.close()


@edit.child()
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(check_author_has_profile)
@lightbulb.option(
    "pronouns",
    "What to change your displayed pronouns to Ex. He/Him, She/Her, They/Them",
    required=True,
)
@lightbulb.command("pronouns", "edit your displayed pronouns")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def pronouns(ctx: lightbulb.SlashContext):
    conn = await get_database_connection()

    new_pronouns = ctx.options.pronouns

    await conn.execute(
        f"UPDATE profiles SET 'pronouns' = '{new_pronouns.title()}' where user_id = {ctx.user.id}"
    )
    await ctx.respond(
        content=f"Displayed pronouns changed to: {new_pronouns.title()}",
        flags=hikari.MessageFlag.EPHEMERAL,
    )
    await conn.close()


# cities = [
#     "Bountiful",
#     "Cottonwood Heights",
#     "Draper",
#     "Eagle Mountain",
#     "Holladay",
#     "Lehi",
#     "Mid Valley (Midvale)",
#     "Murray",
#     "Ogden",
#     "Orem",
#     "Park City",
#     "Provo",
#     "SLC Metro",
#     "SLC Suburbs",
#     "Sandy",
#     "Spanish Fork",
#     "Taylorsville",
#     "Tooele",
#     "West Valley",
#     "West/South Jordan",
#     "Prefer Not To Say",
# ]
#
#
# @edit.child()
# @lightbulb.app_command_permissions(dm_enabled=False)
# @lightbulb.add_checks(check_author_has_profile)
# @lightbulb.option(
#     "location", "What to change your location to", choices=cities, required=True
# )
# @lightbulb.command("location", "edit your location")
# @lightbulb.implements(lightbulb.SlashSubCommand)
# async def location(ctx: lightbulb.SlashContext):
#     conn = await get_database_connection()
#
#     new_location = ctx.options.location
#
#     await conn.execute(
#         f"UPDATE profiles SET location = '{new_location}' where id = {ctx.user.id}"
#     )
#     await ctx.respond(
#         content=f"Displayed location changed to: {new_location}",
#         flags=hikari.MessageFlag.EPHEMERAL,
#     )
#     await conn.close()


# schools = [
#     "Prefer Not To Say",
#     "No Affiliation",
#     "Neumont College of Computer Science",
#     "University of Utah",
#     "Utah Valley University",
#     "Brigham Young University",
#     "Salt Lake Community College",
# ]
#
#
# @edit.child()
# @lightbulb.app_command_permissions(dm_enabled=False)
# @lightbulb.add_checks(check_author_has_profile)
# @lightbulb.option(
#     "proof",
#     "Any document that shows your new school affiliation like a school id for example",
#     type=hikari.Attachment,
#     required=True,
# )
# @lightbulb.option(
#     "affiliation",
#     "What to change your school affiliation to",
#     choices=schools,
#     required=True,
# )
# @lightbulb.command("affiliation", "edit your school affiliation")
# @lightbulb.implements(lightbulb.SlashSubCommand)
# async def affiliation(ctx: lightbulb.SlashContext):
#     new_school = ctx.options.affiliation.title()
#     proof = ctx.options.proof
#     proof: hikari.Attachment
#     if "image" not in proof.media_type:
#         await ctx.respond(
#             content=f"An image file that discord recognizes was not attached",
#             flags=hikari.MessageFlag.EPHEMERAL,
#         )
#         return
#
#     await ctx.respond(
#         content=f"Affiliation will be changed to `{new_school}` with admin approval",
#         flags=hikari.MessageFlag.EPHEMERAL,
#     )
#     btns = await flare.Row(ButtonApproveChange(prof_id=ctx.user.id, change_type="school", change_to=new_school),
#                            ButtonDenyChange(prof_id=ctx.user.id))
#
#     embed = hikari.Embed(
#         title="Affiliation Change",
#         description=f"User: {ctx.user.mention} has requested to have their school affiliation changed to {new_school}",
#     )
#     embed.set_image(proof)
#
#     await ctx.bot.rest.create_message(
#         channel=await get_prof_approv_chn_id(), embed=embed, components=[btns]
#     )


@edit.child()
@lightbulb.app_command_permissions(dm_enabled=False)
@lightbulb.add_checks(check_author_has_profile)
@lightbulb.option(
    "profileimage",
    "What to change your profile image to",
    type=hikari.Attachment,
    required=True,
)
@lightbulb.command("profileimage", "edit your profile image")
@lightbulb.implements(lightbulb.SlashSubCommand)
async def profile_image(ctx: lightbulb.SlashContext):
    conn = await get_database_connection()

    profileimage = ctx.options.profileimage
    profileimage: hikari.Attachment
    new_profileimage = None

    async with profileimage.stream() as stream:
        new_profileimage = await stream.read()

    if "image" not in profileimage.media_type:
        await ctx.respond(
            content=f"An image file that discord recognizes was not attached",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        return

    await ctx.respond(
        content=f"Your profile image will be changed with admin approval",
        flags=hikari.MessageFlag.EPHEMERAL,
    )

    dm_embed = hikari.Embed(
        title="Image Storage Reference",
        description="The bot uses this image reference to generate embeds without having to store the image locally or through a proxy.",
    )
    dm_embed.set_image(new_profileimage)
    msg = await ctx.bot.rest.create_message(
        channel=await ctx.bot.rest.create_dm_channel(ctx.user.id),
        embed=dm_embed
    )
    new_img_url = msg.embeds[0].image.url
    await conn.execute(
        fr"update profiles set 'tmp_img_url'='{new_img_url}' where user_id={ctx.user.id}"
    )

    # TODO: Change to flare buttons
    btns = await flare.Row(
        ButtonApproveChange(prof_id=ctx.user.id, change_type="profile_image_url", change_to="image_from_database"),
        ButtonDenyChange(prof_id=ctx.user.id))

    embed = hikari.Embed(
        title="Profile Image Change",
        description=f"User: {ctx.user.mention} has requested to have their profile image changed\nOld profile image is the embed's top right thumbnail",
    )
    embed.set_image(profileimage)
    row = await conn.fetchrow(
        fr"SELECT 'Profile_Picture' FROM profiles where user_id='{ctx.user.id}'"
    )
    url = row.get("profile_image_url")
    embed.set_thumbnail(url)
    approve_chnl_id = await conn.fetchval(f"Select approval_channel_id from guilds where guild_id={ctx.guild_id}")
    await ctx.bot.rest.create_message(
        channel=approve_chnl_id, embed=embed, components=[btns]
    )
    await conn.close()


@profile_edit_pl.command()
@lightbulb.option("user", "User to see their profile", type=hikari.User, required=False)
@lightbulb.command("viewprofile", "See a user's profile")
@lightbulb.implements(lightbulb.SlashCommand)
async def cmd_viewProfile(ctx: lightbulb.SlashContext):
    conn = await get_database_connection()
    user = None
    if ctx.options.user:
        user = ctx.options.user
    else:
        user = ctx.user

    row = await conn.fetchrow(
        f"SELECT user_id from profiles where user_id={user.id} and stage=7"
    )

    if row and row.get("id"):  # If user has a good profile, return
        await ctx.respond(
            embed=await create_profile_embed(user.id),
            flags=hikari.MessageFlag.EPHEMERAL,
        )
    else:
        await ctx.respond(
            flags=hikari.MessageFlag.EPHEMERAL,
            content=f"{user.mention} has not created their profile or does not have an approved profile",
        )
    await conn.close()


def load(bot: lightbulb.BotApp):
    bot.add_plugin(profile_edit_pl)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(profile_edit_pl)
