import asyncio
import itertools

import asyncpg
import flare
import hikari
import lightbulb

from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import buildPostEmbed
from BotCode.interactions.modals import ModalPostEdit

selects_plugin = lightbulb.Plugin("Editing Selects")


@flare.select(
    placeholder="Select 1 To Edit Before Sending",
    options=[
        hikari.SelectMenuOption(
            label="title",
            description="The post's title",
            value="title",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="description",
            description="The post's description",
            value="description",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="condition",
            description="Condition of item or willing to buy cond.",
            value="condition",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="price/cost",
            description="Price of item or amount willing to pay",
            value="price",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="meetup",
            description="How will interested party get the item",
            value="meetup",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="payment methods",
            description="Payment methods to send/receive payment",
            value="payment_methods",
            emoji=None,
            is_default=False,
        ),
        # hikari.SelectMenuOption(
        #     label="images",
        #     description="Photo(s) for your post",
        #     value="images",
        #     emoji=None,
        #     is_default=False,
        # ),
    ],
    min_values=1,
    max_values=1,
)
async def edit_select_menu(ctx: flare.MessageContext, post_id: int = 0, post_type: str = "No Type",
                           guild_id: hikari.Snowflake = 123):
    if len(ctx.values) == 0:
        await ctx.respond("Select nothing. Please select an item")

    option = ctx.values[0]

    match option:
        case "title":
            modal = ModalPostEdit(post_id=post_id, post_type=post_type, guild_id=guild_id, edit_option="title")
            modal.append(
                flare.TextInput(
                    label="Title",
                    placeholder="New Post Title",
                    style=hikari.TextInputStyle.SHORT,
                )
            )
            await modal.send(ctx.interaction)
        case "description":
            modal = ModalPostEdit(post_id=post_id, post_type=post_type, guild_id=guild_id, edit_option="description")
            modal.append(
                flare.TextInput(
                    label="Description",
                    placeholder="New Post Description",
                    style=hikari.TextInputStyle.PARAGRAPH,
                )
            )
            await modal.send(ctx.interaction)
        case "condition":
            await ctx.message.edit(components=[])
            await ctx.respond(embed=hikari.Embed(
                title="Item Condition",
                description="Select the item's condition if selling or worse condition you would buy\n",

                color=0xFFDD00,
            ), components=await asyncio.gather(
                flare.Row(
                    edit_condition_select_menu(
                        post_type=post_type, post_id=post_id, guild_id=guild_id
                    )
                ))
            )
        case "price":
            modal = ModalPostEdit(post_id=post_id, post_type=post_type, guild_id=guild_id, edit_option="price")
            modal.append(
                flare.TextInput(
                    label="Price/Cost",
                    placeholder="Price of item or amount willing to pay",
                    style=hikari.TextInputStyle.SHORT,
                )
            )
            await modal.send(ctx.interaction)
        case "meetup":
            await ctx.message.edit(components=[])
            await ctx.respond(embed=hikari.Embed(
                title="How will interested party get/sell item",
                description="The options on how the interested party will be able to get/sell the item\n",

                color=0xFFDD00,
            ), components=await asyncio.gather(
                flare.Row(
                    edit_meetup_select_menu(
                        post_type=post_type, post_id=post_id, guild_id=guild_id
                    )
                ))
            )
        case "payment_methods":
            await ctx.message.edit(components=[])
            await ctx.respond(embed=hikari.Embed(
                title="Preferred Payment Methods",
                description="The payment methods you can use for sending or receiving payments\n",

                color=0xFFDD00,
            ), components=await asyncio.gather(
                flare.Row(
                    edit_payment_methods_select_menu(
                        post_type=post_type, post_id=post_id, guild_id=guild_id
                    )
                ))
            )
        # case "images":
        #     from BotCode.interactions.buttons.buttons_posts import ButtonNoPhoto, ButtonCancel
        #
        #     conn = await get_database_connection()
        #     conn: asyncpg.Connection
        #
        #     await conn.execute(
        #         f"UPDATE {post_type} set stage=2 where id={post_id}"
        #     )
        #     embed = hikari.Embed(
        #         title="Send the new photo(s) in one message",
        #         description="Try to post a photo that shows as much of the item as possible and is not blurry. You may add multiple photos at once to your message.  The first attached image will be the main one showed on the post",
        #         color=0xFFDD00,
        #     )
        #     await ctx.message.edit(components=[])
        #     await ctx.respond(
        #         embed=embed,
        #         component=await flare.Row(
        #             ButtonNoPhoto(post_id=post_id, post_type=post_type, guild_id=guild_id),
        #             ButtonCancel(post_id=post_id, post_type=post_type, label="Cancel Post")
        #         ),
        #     )
        #
        #     await conn.close()


@flare.select(
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
async def edit_condition_select_menu(
        ctx: flare.MessageContext, post_id: int = 0, post_type: str = "No Type", guild_id: hikari.Snowflake = 123
):
    from BotCode.interactions.buttons.buttons_posts import ButtonSendPostToMods, ButtonCancel, ButtonNewPostPhotos
    await ctx.defer(False)
    await ctx.message.edit(components=[])
    conn = await get_database_connection()
    conn: asyncpg.Connection

    condition = ctx.values[0]

    resp_code = await conn.execute(
        f"UPDATE {post_type} set condition='{condition}' where id = {post_id}"
    )
    if resp_code == "UPDATE 0":
        await conn.close()
        return
    received_embed = hikari.Embed(title="Received Value", description=condition)

    embed = await buildPostEmbed(
        post_id=post_id, post_type=post_type, user=ctx.user
    )
    await ctx.respond(embeds=[received_embed, embed], components=await asyncio.gather(
        flare.Row(edit_select_menu(post_id=post_id, post_type=post_type, guild_id=guild_id)),
        flare.Row(
            ButtonSendPostToMods(post_id=post_id, post_type=post_type, guild_id=guild_id),
            ButtonNewPostPhotos(post_id=post_id, post_type=post_type, guild_id=guild_id),
            ButtonCancel(post_id=post_id, post_type=post_type, label="Cancel")
        )))


@flare.select(
    placeholder="Select Any Amount",
    options=[
        "Can Deliver (Free)",
        "Can Deliver (Paid)",
        "Can Pickup (Free)",
        "Can Pickup (Paid)",
        "Meet Up",
        "Shipping (Add. Cost)",
        "Shipping (No Add. Cost)"
    ],
    min_values=1,
    max_values=5,
)
async def edit_meetup_select_menu(
        ctx: flare.MessageContext, post_id: int = 0, post_type: str = "No Type", guild_id: hikari.Snowflake = 123
):
    from BotCode.interactions.buttons.buttons_posts import ButtonSendPostToMods, ButtonCancel, ButtonNewPostPhotos
    await ctx.defer(False)
    await ctx.message.edit(components=[])
    conn = await get_database_connection()
    conn: asyncpg.Connection

    selected = ""
    for value in ctx.values:
        selected = selected.__add__(f"{value}, ")
    selected = selected.removesuffix(", ")

    resp_code = await conn.execute(
        f"UPDATE {post_type} set meetup='{selected}' where id = {post_id}"
    )
    if resp_code == "UPDATE 0":
        await conn.close()
        return
    received_embed = hikari.Embed(title="Received Value", description=selected)

    embed = await buildPostEmbed(
        post_id=post_id, post_type=post_type, user=ctx.user
    )
    await ctx.respond(embeds=[received_embed, embed], components=await asyncio.gather(
        flare.Row(edit_select_menu(post_id=post_id, post_type=post_type, guild_id=guild_id)),
        flare.Row(
            ButtonSendPostToMods(post_id=post_id, post_type=post_type, guild_id=guild_id),
            ButtonNewPostPhotos(post_id=post_id, post_type=post_type, guild_id=guild_id),
            ButtonCancel(post_id=post_id, post_type=post_type, label="Cancel")
        )))


@flare.select(
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
async def edit_payment_methods_select_menu(
        ctx: flare.MessageContext, post_id: int = 0, post_type: str = "No Type", guild_id: hikari.Snowflake = 123
):
    from BotCode.interactions.buttons.buttons_posts import ButtonSendPostToMods, ButtonCancel, ButtonNewPostPhotos
    await ctx.defer(False)
    await ctx.message.edit(components=[])
    conn = await get_database_connection()
    conn: asyncpg.Connection

    pay_meth = ""
    for value in ctx.values:
        pay_meth = pay_meth.__add__(f"{value}, ")
    pay_meth = pay_meth.removesuffix(", ")

    resp_code = await conn.execute(
        f"UPDATE {post_type} set payment_methods='{pay_meth}' where id = {post_id}"
    )
    if resp_code == "UPDATE 0":
        await conn.close()
        return
    received_embed = hikari.Embed(title="Received Value", description=pay_meth)

    embed = await buildPostEmbed(
        post_id=post_id, post_type=post_type, user=ctx.user
    )
    await ctx.respond(embeds=[received_embed, embed], components=await asyncio.gather(
        flare.Row(edit_select_menu(post_id=post_id, post_type=post_type, guild_id=guild_id)),
        flare.Row(
            ButtonSendPostToMods(post_id=post_id, post_type=post_type, guild_id=guild_id),
            ButtonNewPostPhotos(post_id=post_id, post_type=post_type, guild_id=guild_id),
            ButtonCancel(post_id=post_id, post_type=post_type, label="Cancel")
        )))


def load(bot: lightbulb.BotApp):
    bot.add_plugin(selects_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(selects_plugin)
