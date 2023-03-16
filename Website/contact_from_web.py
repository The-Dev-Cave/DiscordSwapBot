import os

import flare
import hikari
import lightbulb

from BotCode.environment.database import get_database_connection
from BotCode.interactions.buttons.buttons_user_bridge import (
    ButtonShowMoreImages,
    ButtonMarkPostSold,
    ButtonCloseUserBridge,
    ButtonMarkPostPending,
)

contact_web_plugin = lightbulb.Plugin("Lightbulb Bot Events")


async def contact_channel_from_web(
    post_id: int, post_type: str, int_party_id: int, restApp: hikari.RESTApp, conn
):
    BOT_TOKEN = os.getenv("BOT_TOKEN")

    post_id = int(post_id)
    int_party_id = int(int_party_id)
    
    async with restApp.acquire(BOT_TOKEN, hikari.TokenType.BOT) as bot_client:
        bot_client: hikari.impl.RESTClientImpl
        # conn = await get_database_connection()
        post_type = post_type.lower()
        print(f"Select * from {post_type} where id={post_id}")
        post = await conn.fetchrow(f"Select * from {post_type} where id={post_id}")
        guild_id = post.get("guild_id")

        guild_data = await conn.fetchrow("Select * from guilds where guild_id=$1", guild_id)

        author_id = int(post.get("author_id"))

        if int_party_id == author_id:
            return  # "You can't create a chat channel with yourself"

        perm_overwrites = [
            hikari.PermissionOverwrite(
                type=hikari.PermissionOverwriteType.MEMBER,
                allow=(
                    hikari.Permissions.VIEW_CHANNEL
                    | hikari.Permissions.READ_MESSAGE_HISTORY
                    | hikari.Permissions.SEND_MESSAGES
                ),
                id=int_party_id,
            ),
            hikari.PermissionOverwrite(
                type=hikari.PermissionOverwriteType.MEMBER,
                allow=(
                    hikari.Permissions.VIEW_CHANNEL
                    | hikari.Permissions.READ_MESSAGE_HISTORY
                    | hikari.Permissions.SEND_MESSAGES
                ),
                id=author_id,
            ),
        ]
        print(guild_id, int_party_id)
        int_part_mem = await bot_client.fetch_member(
            guild=guild_id, user=int_party_id  # print out data
        )

        user_name = int_part_mem.display_name

        channels = {
            "sell": guild_data.get("sell_channel_id"),
            "buy": guild_data.get("buy_channel_id"),
        }

        msg_url = (
            await bot_client.fetch_message(
                channels.get(post_type), post.get("message_id")
            )
        ).make_link(guild_id)

        channel_name = f"{user_name[0:10]}-{post_id}"

        swap_cat_id = await conn.fetchval(
            f"Select user_bridge_cat_id from guilds where guild_id={guild_id}"
        )

        channel = await bot_client.create_guild_text_channel(
            guild=guild_id,
            name=channel_name,
            permission_overwrites=perm_overwrites,
            category=swap_cat_id,
        )
        embed = hikari.Embed(
            title="Welcome to the user bridge!",
            description=f"Only the lister can mark as pending or sold and neither will close the channel\nMarking as sold will close other channels connect to this post\nRun `/viewprofile user` to see basic info about the other person and their photo for identification\n[Link to Original Post]({msg_url})",
            color=0x00FF00,
            url=msg_url,
        )
        row = None
        if post_type == "sell":
            row = await conn.fetchrow(
                f"SELECT add_images from {post_type} where id={post_id}"
            )

        if row and row.get("add_images"):
            btns_row = await flare.Row(
                ButtonShowMoreImages(post_id=post_id, post_type=post_type),
                ButtonMarkPostPending(
                    post_id=post_id, post_type=post_type, post_owner_id=author_id
                ),
                ButtonMarkPostSold(
                    post_id=post_id,
                    post_type=post_type,
                    post_owner_id=author_id,
                    int_party_id=int_party_id,
                ),
                ButtonCloseUserBridge(
                    post_id=post_id,
                    post_type=post_type,
                    post_owner_id=author_id,
                    int_party_id=int_party_id,
                ),
            )
        else:
            btns_row = await flare.Row(
                ButtonMarkPostPending(
                    post_id=post_id, post_type=post_type, post_owner_id=author_id
                ),
                ButtonMarkPostSold(
                    post_id=post_id,
                    post_type=post_type,
                    post_owner_id=author_id,
                    int_party_id=int_party_id,
                ),
                ButtonCloseUserBridge(
                    post_id=post_id,
                    post_type=post_type,
                    post_owner_id=author_id,
                    int_party_id=int_party_id,
                ),
            )

        await channel.send(embed=embed, component=btns_row)

        await channel.send(
            content=f"Listing: **{post.get('title')}**\nLister: <@{author_id}>\nInterested Party: {int_part_mem.mention}",
            user_mentions=True,
        )
        await conn.close()


def load(bot):
    bot.add_plugin(contact_web_plugin)


def unload(bot):
    bot.remove_plugin(contact_web_plugin)
