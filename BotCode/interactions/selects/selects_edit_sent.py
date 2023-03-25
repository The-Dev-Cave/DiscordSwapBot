import asyncio
import itertools

import asyncpg
import flare
import hikari
import lightbulb

from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import buildPostEmbed

selects_sent_edit_plugin = lightbulb.Plugin("Selects")


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
async def condition_edit_select_menu(
    ctx: flare.MessageContext,
    post_id: int = 0,
    post_type: str = "No Type",
):
    from BotCode.functions.send_logs import send_public_log

    user_input = ctx.values[0]

    await ctx.edit_response(
        components=[],
        content="Post is being edited. Free to dismiss message",
        embeds=[],
    )
    conn = await get_database_connection()
    conn: asyncpg.Connection

    post = await conn.fetchrow(
        f"SELECT message_id,guild_id from {post_type} where id={post_id}"
    )
    guild = await conn.fetchrow(
        f"SELECT buy_channel_id, sell_channel_id from guilds where guild_id={post.get('guild_id')}"
    )

    await conn.execute(
        f"UPDATE {post_type} set condition='{user_input}' where id={post_id}"
    )

    embed = await buildPostEmbed(post_id=post_id, post_type=post_type, user=ctx.user)

    chnl_dict = {
        "sell": guild.get("sell_channel_id"),
        "buy": guild.get("buy_channel_id"),
    }

    msg = await selects_sent_edit_plugin.bot.rest.fetch_message(
        channel=chnl_dict.get(post_type), message=post.get("message_id")
    )
    await msg.edit(embeds=[embed], attachments=None)

    await send_public_log(
        post.get("guild_id"),
        f"**{post_type.upper()}:** <@{post.get('author_id')}> **UPDATED** listing __{post.get('title')}__ with a new **CONDITION**",
    )


@flare.text_select(
    placeholder="Select Any Amount",
    options=[
        "Deliver (Free)",
        "Deliver (Paid)",
        "Pickup (Free)",
        "Pickup (Paid)",
        "Meet Up",
        "Shipping (Add. Cost)",
        "Shipping (No Add. Cost)",
    ],
    min_values=1,
    max_values=5,
)
async def meetup_edit_select_menu(
    ctx: flare.MessageContext,
    post_id: int = 0,
    post_type: str = "No Type",
):
    from BotCode.functions.send_logs import send_public_log

    selected = ""
    for value in ctx.values:
        selected = selected.__add__(f"{value}, ")
    user_input = selected.removesuffix(", ")

    await ctx.edit_response(
        components=[],
        content="Post is being edited. Free to dismiss message",
        embeds=[],
    )
    conn = await get_database_connection()
    conn: asyncpg.Connection

    post = await conn.fetchrow(
        f"SELECT message_id,guild_id,title,author_id from {post_type} where id={post_id}"
    )
    guild = await conn.fetchrow(
        f"SELECT buy_channel_id, sell_channel_id from guilds where guild_id={post.get('guild_id')}"
    )

    await conn.execute(f"UPDATE {post_type} set meetup='{user_input}' where id={post_id}")

    embed = await buildPostEmbed(post_id=post_id, post_type=post_type, user=ctx.user)

    chnl_dict = {
        "sell": guild.get("sell_channel_id"),
        "buy": guild.get("buy_channel_id"),
    }

    msg = await selects_sent_edit_plugin.bot.rest.fetch_message(
        channel=chnl_dict.get(post_type), message=post.get("message_id")
    )
    await msg.edit(embeds=[embed], attachments=None)

    await send_public_log(
        post.get("guild_id"),
        f"**{post_type.upper()}:** <@{post.get('author_id')}> **UPDATED** listing __{post.get('title')}__ with new **ITEM TRANSACTION(S)**",
    )


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
async def edit_payment_methods_select_menu(
    ctx: flare.MessageContext,
    post_id: int = 0,
    post_type: str = "No Type",
):
    from BotCode.functions.send_logs import send_public_log

    selected = ""
    for value in ctx.values:
        selected = selected.__add__(f"{value}, ")
    user_input = selected.removesuffix(", ")

    await ctx.edit_response(
        components=[],
        content="Post is being edited. Free to dismiss message",
        embeds=[],
    )
    conn = await get_database_connection()
    conn: asyncpg.Connection

    post = await conn.fetchrow(
        f"SELECT message_id,guild_id,title,author_id from {post_type} where id={post_id}"
    )
    guild = await conn.fetchrow(
        f"SELECT buy_channel_id, sell_channel_id from guilds where guild_id={post.get('guild_id')}"
    )

    await conn.execute(f"UPDATE {post_type} set payment_methods='{user_input}' where id={post_id}")

    embed = await buildPostEmbed(post_id=post_id, post_type=post_type, user=ctx.user)

    chnl_dict = {
        "sell": guild.get("sell_channel_id"),
        "buy": guild.get("buy_channel_id"),
    }

    msg = await selects_sent_edit_plugin.bot.rest.fetch_message(
        channel=chnl_dict.get(post_type), message=post.get("message_id")
    )
    await msg.edit(embeds=[embed], attachments=None)

    await send_public_log(
        post.get("guild_id"),
        f"**{post_type.upper()}:** <@{post.get('author_id')}> **UPDATED** listing __{post.get('title')}__ with new **PAYMENT METHOD(S)**",
    )


def load(bot: lightbulb.BotApp):
    bot.add_plugin(selects_sent_edit_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(selects_sent_edit_plugin)
