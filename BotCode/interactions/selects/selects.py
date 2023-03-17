import asyncio
import itertools

import asyncpg
import flare
import hikari
import lightbulb

from BotCode.environment.database import get_database_connection
from BotCode.functions.send_logs import send_public_log

selects_plugin = lightbulb.Plugin("Selects")


# @flare.text_select(
#     placeholder="Select The School You Are Affiliated With",
#     options=[
#         "Prefer Not To Say",
#         "No Affiliation",
#         "Neumont College of Computer Science",
#         "University of Utah",
#         "Utah Valley University",
#         "Brigham Young University",
#         "Salt Lake Community College",
#     ],
# )
# async def school_select_menu(ctx: flare.MessageContext):
#     await ctx.message.edit(components=[], content=f"Affiliation: {ctx.values[0]}")
#     # noinspection PyTypeChecker
#     await ctx.respond(
#         f"Where are you mainly located?",
#         components=await asyncio.gather(
#             flare.Row(city_select_menu(for_profile=True)),
#         ),
#     )
#
#     conn = await get_database_connection()
#     conn: asyncpg.Connection
#
#     await conn.execute(
#         f"UPDATE profiles set school='{ctx.values[0]}' where id={ctx.user.id}"
#     )
#
#     await conn.close()


# noinspection PyTypeChecker
# @flare.text_select(
#     placeholder="Select City You Mainly Live In",
#     options=[
#         "Bountiful",
#         "Cottonwood Heights",
#         "Draper",
#         "Eagle Mountain",
#         "Holladay",
#         "Lehi",
#         "Mid Valley (Midvale)",
#         "Murray",
#         "Ogden",
#         "Orem",
#         "Park City",
#         "Provo",
#         "SLC Metro",
#         "SLC Suburbs",
#         "Sandy",
#         "Spanish Fork",
#         "Taylorsville",
#         "Tooele",
#         "West Valley",
#         "West/South Jordan",
#         "Prefer Not To Say",
#     ],
# )
# async def city_select_menu(
#         ctx: flare.MessageContext,
#         for_profile: bool = True,
#         post_id: int = 0,
#         post_type: str = "No Type",
# ):
#     conn = await get_database_connection()
#     conn: asyncpg.Connection
#
#     selected_value = ctx.values[0]
#     user_id = ctx.user.id
#
#     if for_profile:
#         await ctx.message.edit(components=[], content=f"City: {ctx.values[0]}")
#         embed = hikari.Embed(
#             title="Send an image that you want to use for your user profile for others to identify you",
#             description="Please have face easily visible and should show shoulders and up. Only one person in the photo.\n It will only be viewable when someone runs the `/viewprofile` command and it IS NOT changing your avatar/pfp for the server itself.",
#         )
#         await ctx.respond(embed=embed)
#
#         await conn.execute(
#             f"UPDATE profiles set location='{selected_value}', stage=2 where id={user_id}"
#         )
#         await conn.close()
#         return
#     else:
#
#         await ctx.message.edit(components=[])
#
#         resp_code = await conn.execute(
#             f"UPDATE {post_type} set location='{selected_value}' where id={post_id}"
#         )
#
#         if resp_code == "UPDATE 0":
#             await conn.close()
#             return
#
#         embed = hikari.Embed(title="Received Value", description=selected_value)
#
#         embed_nextpart = hikari.Embed(
#             title="How will the transaction occur?",
#             description="The options on how the interested party will be able to get/sell the item",
#             color=0xFFDD00,
#         )
#         await ctx.respond(
#             embeds=[embed, embed_nextpart],
#             components=await asyncio.gather(
#                 flare.Row(meetup_select_menu(post_id=post_id, post_type=post_type))
#             ),
#         )
#
#     await conn.close()


# noinspection PyTypeChecker
@flare.text_select(
    placeholder="Select Condition",
    options=[
        hikari.SelectMenuOption(
            label="New",
            description="Item is new in box or never used",
            value="New\nItem is new in box or never used",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Like New",
            description="Item looks and functions as if it was new.",
            value="Like New\nItem looks and functions as if it was new.",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Lightly Used",
            description="Item shows light signs of use, but are generally unnoticeable.",
            value="Lightly Used\nItem shows light signs of use, but are generally unnoticeable.",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Used",
            description="Item shows signs of use, but functions normally",
            value="Used\nItem shows signs of use, but functions normally",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Worn",
            description="Item shows signs of heavy use, but functions normally.",
            value="Worn\nItem shows signs of heavy use, but functions normally.",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Some Damage",
            description="Item has noticeable damage, and mostly functions normally.",
            value="Some Damage\nItem has noticeable damage, and mostly functions normally.",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Damaged",
            description="Item mostly functions, and has sustained heavy damage.",
            value="Damaged\nItem mostly functions, and has sustained heavy damage.",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Parts Only",
            description="Item does not function or can only be salvaged.",
            value="Parts Only\nItem does not function or can only be salvaged.",
            emoji=None,
            is_default=False,
        ),
    ],
)
async def condition_select_menu(
    ctx: flare.MessageContext,
    post_id: int = 0,
    post_type: str = "No Type",
    guild_id: hikari.Snowflake = 123,
):
    from BotCode.interactions.buttons.buttons_posts import ButtonCancel
    await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
    conn = await get_database_connection()
    conn: asyncpg.Connection

    condition = ctx.values[0]

    await ctx.message.edit(components=[])
    resp_code = await conn.execute(
        f"UPDATE {post_type} set condition='{condition}' where id = {post_id}"
    )
    if resp_code == "UPDATE 0":
        await conn.close()
        return
    embed = hikari.Embed(title="Received Value", description=condition)
    embed_nextpart = hikari.Embed(
        title="How will the transaction occur?",
        description="The options on how the interested party will be able to get/sell the item",
        color=0xFFDD00,
    )

    await ctx.respond(
        embeds=[embed, embed_nextpart],
        components=await asyncio.gather(
            flare.Row(
                meetup_select_menu(
                    post_type=post_type, post_id=post_id, guild_id=guild_id
                )
            ),
            flare.Row(
                ButtonCancel(post_id=post_id, post_type=post_type, label="Cancel")
            ),
        ),
    )
    await conn.close()


# noinspection PyTypeChecker
@flare.text_select(
    placeholder="Select Any Amount",
    options=[
        "Can Deliver (Free)",
        "Can Deliver (Paid)",
        "Can Pickup (Free)",
        "Can Pickup (Paid)",
        "Meet Up",
        "Shipping (Add. Cost)",
        "Shipping (No Add. Cost)",
    ],
    min_values=1,
    max_values=5,
)
async def meetup_select_menu(
    ctx: flare.MessageContext,
    post_id: int = 0,
    post_type: str = "No Type",
    guild_id: hikari.Snowflake = 123,
):
    from BotCode.interactions.buttons.buttons_posts import ButtonNoPhoto
    from BotCode.interactions.buttons.buttons_posts import ButtonCancel
    await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
    conn = await get_database_connection()
    conn: asyncpg.Connection

    selected = ""
    for value in ctx.values:
        selected = selected.__add__(f"{value}, ")
    selected = selected.removesuffix(", ")

    embed = hikari.Embed(title="Received Values", description=selected)

    await ctx.message.edit(components=[])
    # if post_type == "trading":
    #     resp_code = await conn.execute(
    #         f"UPDATE {post_type} set meetup='{selected}', stage=2 where id = {post_id}"
    #     )
    #     if resp_code == "UPDATE 0":
    #         await conn.close()
    #         return
    #     embed_nextpart = hikari.Embed(
    #         title="Would you like to add a photo(s) of your item?",
    #         description="Try to post a photo that shows as much of the item as possible and is not blurry. You may add multiple photos at once to your message.  The first attached image will be the main one showed on the post",
    #         color=0xFFDD00,
    #     )
    #     await ctx.respond(
    #         embeds=[embed, embed_nextpart],
    #         component=await flare.Row(
    #             ButtonNoPhoto(post_id=post_id, post_type=post_type, guild_id=guild_id)
    #         ),
    #     )
    # else:
    resp_code = await conn.execute(
        f"UPDATE {post_type} set meetup='{selected}' where id = {post_id}"
    )
    if resp_code == "UPDATE 0":
        await conn.close()
        return
    embed_nextpart = hikari.Embed(
        title="Preferred Payment Methods",
        description="The payment methods you can use for sending or receiving payments",
        color=0xFFDD00,
    )

    await ctx.respond(
        embeds=[embed, embed_nextpart],
        components=await asyncio.gather(
            flare.Row(
                payment_methods_select_menu(
                    post_type=post_type, post_id=post_id, guild_id=guild_id
                )
            ),
            flare.Row(
                ButtonCancel(post_id=post_id, post_type=post_type, label="Cancel")
            ),
        ),
    )
    await conn.close()


@flare.text_select(
    placeholder="Select Payment Methods",
    options=[
        "Cash",
        "Paypal",
        "Venmo",
        "CashApp",
        "Google Pay",
        "Apple Pay",
        "Samsung Pay",
        "Check",
        "Wire Transfer",
    ],
    min_values=1,
    max_values=5,
)
async def payment_methods_select_menu(
    ctx: flare.MessageContext,
    post_id: int = 0,
    post_type: str = "No Type",
    guild_id: hikari.Snowflake = 123,
):
    from BotCode.interactions.buttons.buttons_posts import (
        ButtonNoPhoto,
        ButtonSendPostToMods,
        ButtonNewPostPhotos,
    )

    from BotCode.functions.embeds import buildPostEmbed
    from BotCode.interactions.buttons.buttons_posts import ButtonCancel
    await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
    conn = await get_database_connection()
    conn: asyncpg.Connection

    pay_meth = ""
    for value in ctx.values:
        pay_meth = pay_meth.__add__(f"{value}, ")
    pay_meth = pay_meth.removesuffix(", ")

    embed = hikari.Embed(title="Received Value(s)", description=pay_meth)
    if post_type == "sell":
        embed_nextstep = hikari.Embed(
            title="Would you like to add a photo(s) of your item?",
            description="Try to post a photo that shows as much of the item as possible and is not blurry. You may add multiple photos at once to your message.  The first attached image will be the main one showed on the post and up to 3 extra photos",
            color=0xFFDD00,
        )
        await ctx.message.edit(components=[])
        resp_code = await conn.execute(
            f"UPDATE {post_type} set payment_methods='{pay_meth}', stage=2 where id={post_id}"
        )
        if resp_code == "UPDATE 0":
            await conn.close()
            return
        msg = await (
            await ctx.respond(
                embeds=[embed, embed_nextstep],
                component=await flare.Row(
                    ButtonNoPhoto(
                        post_id=post_id, post_type=post_type, guild_id=guild_id
                    ),
                    ButtonCancel(post_id=post_id, post_type=post_type, label="Cancel"),
                ),
            )
        ).retrieve_message()
        await conn.execute(
            f"UPDATE {post_type} set image='{msg.id}' where id={post_id}"
        )

    else:
        resp_code = await conn.execute(
            f"UPDATE {post_type} set payment_methods='{pay_meth}' where id={post_id}"
        )
        if resp_code == "UPDATE 0":
            await conn.close()
            return
        embed = await buildPostEmbed(
            post_id=post_id, post_type=post_type, user=ctx.user
        )
        await ctx.message.edit(components=[])
        from BotCode.interactions.selects.selects_editing import edit_select_menu

        await ctx.respond(
            embed=embed,
            components=await asyncio.gather(
                flare.Row(
                    edit_select_menu(
                        post_id=post_id, post_type=post_type, guild_id=guild_id
                    )
                ),
                flare.Row(
                    ButtonSendPostToMods(
                        post_id=post_id, post_type=post_type, guild_id=guild_id
                    ),
                    ButtonCancel(post_id=post_id, post_type=post_type, label="Cancel"),
                ),
            ),
        )

    await conn.close()

    # condition = ctx.values[0]
    #
    # await conn.execute(
    #     f"UPDATE {post_type} set condition='{condition}' where id = {post_id}"
    # )
    #
    # embed = hikari.Embed(title="Received Value", description=condition)
    # embed_nextpart = hikari.Embed(
    #     title="Where are you located?",
    #     description="Choose the location that best represents where you live or close to where meetup/pick up would be",
    #     color=0xFFDD00,
    # )
    #
    # await ctx.message.edit(components=[])
    # await ctx.respond(
    #     embeds=[embed, embed_nextpart],
    #     components=await asyncio.gather(
    #         flare.Row(
    #             city_select_menu(
    #                 for_profile=False, post_type=post_type, post_id=post_id
    #             )
    #         )
    #     ),
    # )
    # await conn.close()


# noinspection PyTypeChecker
@flare.text_select(
    placeholder="Select What To Update",
    options=[
        hikari.SelectMenuOption(
            label="Edit Post (Not Implemented)",
            value="edit",
            description="Edit post information (Not Implemented)",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="(Un)Mark As Pending",
            value="pending",
            description="Mark post as pending",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Mark As Sold",
            value="sold",
            description="Mark sold in log & delete post",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Remove Listing",
            value="remove",
            description="Remove listing, but not sold",
            emoji=None,
            is_default=False,
        ),
    ],
)
async def update_post(
    ctx: flare.MessageContext, post_id: int = 0, post_type: str = "No Type"
):
    conn = await get_database_connection()
    selcected_value = ctx.values[0]
    row = await conn.fetchrow(
        f"Select buy_channel_id,sell_channel_id,user_bridge_cat_id from guilds where guild_id={ctx.guild_id}"
    )
    swap_cat_id = row.get("user_bridge_cat_id")
    # Change select menu for edit post to choose what to edit
    # Change to button to ask if sure to change pending, sold, or to remove
    #   and let them know to click dismiss message to cancel / finish
    match selcected_value:
        case "edit":
            await ctx.edit_response(content="Not implemented yet", components=[])
            await ctx.edit_response(
                component=await asyncio.gather(
                    flare.Row(edit_post(post_id=post_id, post_type=post_type)),
                )
            )
        case "pending":

            post_types_dict = {
                "sell": row.get("sell_channel_id"),
                "buy": row.get("buy_channel_id"),
            }

            try:
                row = await conn.fetchrow(
                    f"Select message_id, post_status, title, author_id from {post_type} where id={post_id}"
                )
                pending = row.get("post_status")

                msg = await ctx.bot.rest.fetch_message(
                    post_types_dict.get(post_type), row.get("message_id")
                )
            except:
                await ctx.respond(
                    "Post no longer able to be marked as pending",
                    flags=hikari.MessageFlag.EPHEMERAL,
                )
                await conn.close()
                return

            if (pending is None) or (int(pending) == int(0)):
                embed = msg.embeds[0]
                embed.__setattr__("color", 0xFF0000)
                embed.__setattr__(
                    "title", embed.__getattribute__("title") + " (Pending)"
                )
                await msg.edit(embed=embed)
                await conn.execute(
                    f"update {post_type} set post_status=1 where id={post_id}"
                )
                await ctx.edit_response(
                    content="Post marked as pending and any open chats have been notified",
                    components=[],
                )
                await send_public_log(
                    guild_id=ctx.guild_id,
                    text=f"**{post_type.upper()}:** <@{row.get('author_id')}> **UPDATED** listing __{row.get('title')}__ to **PENDING**",
                )
                channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)

                test2 = itertools.groupby(
                    filter(
                        lambda c: isinstance(c[1], hikari.GuildTextChannel),
                        channels.items(),
                    ),
                    key=lambda c: c[1].parent_id,
                )
                for item in test2:
                    cat_id = item[0]
                    if cat_id == swap_cat_id:
                        for i in item[1]:
                            if (str(i[1].name).endswith(str(post_id))) and (
                                str(i[0]) != str(ctx.channel_id)
                            ):
                                await ctx.bot.rest.create_message(
                                    channel=i[0],
                                    embed=hikari.Embed(
                                        title="Post has been marked as **PENDING**",
                                        description="",
                                        color=0xFFDD00,
                                    ),
                                )
                        break

            else:
                embed = msg.embeds[0]
                embed.__setattr__("color", 0xFFDD00)
                embed.__setattr__("title", row.get("title"))
                await msg.edit(embed=embed)
                await conn.execute(
                    f"update {post_type} set post_status=0 where id={post_id}"
                )
                await ctx.edit_response(
                    content="Post no longer marked as pending", components=[]
                )
                channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)
                await send_public_log(
                    guild_id=ctx.guild_id,
                    text=f"**{post_type.upper()}:** <@{row.get('author_id')}> **UPDATED** listing __{row.get('title')}__ to **AVAILABLE**",
                )

                test2 = itertools.groupby(
                    filter(
                        lambda c: isinstance(c[1], hikari.GuildTextChannel),
                        channels.items(),
                    ),
                    key=lambda c: c[1].parent_id,
                )
                for item in test2:
                    cat_id = item[0]
                    if cat_id == swap_cat_id:
                        for i in item[1]:
                            if (str(i[1].name).endswith(str(post_id))) and (
                                str(i[0]) != str(ctx.channel_id)
                            ):
                                await ctx.bot.rest.create_message(
                                    channel=i[0],
                                    embed=hikari.Embed(
                                        title="Post has been marked as **AVAILABLE**",
                                        description="",
                                        color=0x00FF00,
                                    ),
                                )
                        break
        case "sold":
            await ctx.edit_response(
                "Post has been marked as sold and removed from respective post channel and user bridge chats related to this post have been closed",
                components=[],
            )

            row = await conn.fetchrow(
                f"SELECT message_id, title, author_id from {post_type} where id={post_id}"
            )
            await send_public_log(
                guild_id=ctx.guild_id,
                text=f"**{post_type.upper()}:** <@{row.get('author_id')}> has **SOLD** listing __{row.get('title')}__",
            )
            await ctx.bot.rest.delete_message(ctx.channel_id, row.get("message_id"))

            channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)

            test2 = itertools.groupby(
                filter(
                    lambda c: isinstance(c[1], hikari.GuildTextChannel),
                    channels.items(),
                ),
                key=lambda c: c[1].parent_id,
            )
            for item in test2:
                cat_id = item[0]
                if cat_id == swap_cat_id:
                    for i in item[1]:
                        if (str(i[1].id) != str(ctx.channel_id)) and (
                            str(post_id) in str(i[1].name)
                        ):
                            await ctx.bot.rest.delete_channel(i[1].id)

            await conn.execute(f"delete from {post_type} where id={post_id}")
        case "remove":
            await ctx.edit_response(
                "Post has been removed from the respective post channel and related user bridge chats have been closed",
                components=[],
            )

            row = await conn.fetchrow(
                f"SELECT message_id, title, author_id from {post_type} where id={post_id}"
            )
            await send_public_log(
                guild_id=ctx.guild_id,
                text=f"**{post_type.upper()}:** <@{row.get('author_id')}> has **REMOVED** listing __{row.get('title')}__",
            )

            await ctx.bot.rest.delete_message(ctx.channel_id, row.get("message_id"))

            channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)
            test2 = itertools.groupby(
                filter(
                    lambda c: isinstance(c[1], hikari.GuildTextChannel),
                    channels.items(),
                ),
                key=lambda c: c[1].parent_id,
            )
            for item in test2:
                cat_id = item[0]
                if cat_id == swap_cat_id:
                    for i in item[1]:
                        if (str(i[1].id) != str(ctx.channel_id)) and (
                            str(post_id) in str(i[1].name)
                        ):
                            await ctx.bot.rest.delete_channel(i[1].id)

            await conn.execute(f"delete from {post_type} where id={post_id}")
    await conn.close()


@flare.text_select(
    placeholder="Choose What To Edit",
    options=[
        # hikari.SelectMenuOption(label="Title", value="title", description="", emoji=None, is_default=False),
        # hikari.SelectMenuOption(label="Description", value="description", description="", emoji=None, is_default=False),
        hikari.SelectMenuOption(
            label="Condition",
            value="condition",
            description="",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Cost/Looking For",
            value="cost_look",
            description="",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Payment Methods",
            value="payment",
            description="",
            emoji=None,
            is_default=False,
        ),
        # hikari.SelectMenuOption(label="Location", value="location", description="", emoji=None, is_default=False),
        # hikari.SelectMenuOption(label="Meetup", value="meetup", description="", emoji=None, is_default=False),
        hikari.SelectMenuOption(
            label="Photos", value="photos", description="", emoji=None, is_default=False
        ),
    ],
)
async def edit_post(
    ctx: flare.MessageContext, post_id: int = 0, post_type: str = "No Type"
):
    await ctx.edit_response("Not Implemented", components=[])
    return
    # match ctx.values[0]:
    #     case "title":
    #         await ctx.bot.rest.create_modal_response(
    #             interaction=ctx.interaction,
    #             token=ctx.interaction.token,
    #             title="Edit Title"
    #         )


def load(bot: lightbulb.BotApp):
    bot.add_plugin(selects_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(selects_plugin)
