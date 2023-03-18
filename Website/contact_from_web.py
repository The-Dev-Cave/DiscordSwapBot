import itertools
import os

import asyncpg
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
        post = await conn.fetchrow(f"Select * from {post_type} where id={post_id}")
        guild_id = post.get("guild_id")

        guild_data = await conn.fetchrow("Select * from guilds where guild_id=$1", guild_id)

        author_id = int(post.get("author_id"))

        if int_party_id == author_id:
            return  # "You can't create a chat channel with yourself"

        member = await bot_client.fetch_member(post.get("guild_id"), int_party_id)

        channel_name = f"{member.display_name[0:10]}-{post_id}".replace(" ", "-").lower()

        # channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)
        channels = await bot_client.fetch_guild_channels(post.get("guild_id"))
        swap_cat_id = await conn.fetchval(
            f"Select user_bridge_cat_id from guilds where guild_id={post.get('guild_id')}"
        )
        chnls_grouped = itertools.groupby(
            filter(
                lambda c: isinstance(c, hikari.GuildTextChannel),
                channels,
            ),
            key=lambda c: c.parent_id,
        )
        for item in chnls_grouped:
            cat_id = item[0]
            if cat_id == swap_cat_id:
                for i in item[1]:
                    if str(i.name) == channel_name:
                        return
                break

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
        int_part_mem = await bot_client.fetch_member(
            guild=guild_id, user=int_party_id
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


async def create_profile_embed(
        userID: hikari.Snowflake | int, guild_id: hikari.Snowflake | int,
        restApp: hikari.RESTApp, conn
) -> hikari.Embed:
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    async with restApp.acquire(BOT_TOKEN, hikari.TokenType.BOT) as bot_client:
        bot_client: hikari.impl.RESTClientImpl
        conn: asyncpg.Connection

        guild_id = int(guild_id)
        userID = int(userID)

        data = await conn.fetchrow(f"SELECT * from profiles where user_id='{userID}'")

        show_ratings = True
        show_profile = True

        if guild_id:
            guild_set = await conn.fetchrow(
                "SELECT * from guilds where guild_id=$1", guild_id
            )
            show_ratings = guild_set.get("ratings_enabled")
            show_profile = guild_set.get("profile_enabled")

        if (not show_ratings) and (not show_profile):
            embed = hikari.Embed(
                title="Profile and Ratings Both Disabled",
                description="This guild has disabled profiles and ratings so they will not be shown.",
            )
            return embed

        if show_profile:
            fname = data.get("first_name")
            lname = data.get("last_name")
            # affiliation = data.get("school")
            # location = data.get("location")
            pronouns = data.get("pronouns")
            image_url = data.get("profile_picture")
            # joined_date = data.get("joined_date").strftime("%m/%d/%Y")
            embed = hikari.Embed(title=f"{fname} {lname}", description="==================")
            embed.set_thumbnail(image_url)
            # embed.add_field("Affiliation:", affiliation, inline=True)
            # embed.add_field("Location:", location, inline=True)
            embed.add_field("Pronouns:", pronouns)
        else:
            user = await bot_client.fetch_user(userID)
            embed = hikari.Embed(
                title=f"{user.username}#{user.discriminator} Ratings",
                description="==================",
            )
            embed.set_thumbnail(user.display_avatar_url)

        if show_ratings:
            row = (await conn.fetch(f"SELECT * FROM profiles where user_id = {userID}"))[0]
            comm_good = int(row.get("comm_rating")[0])
            comm_total = int(row.get("comm_rating")[1])
            resp_good = int(row.get("resp_rating")[0])
            resp_total = int(row.get("resp_rating")[1])
            pricing_good = int(row.get("price_rating")[0])
            pricing_total = int(row.get("price_rating")[1])
            ontime_good = int(row.get("punct_rating")[0])
            ontime_total = int(row.get("punct_rating")[1])
            acc_good = int(row.get("acc_rating")[0])
            acc_total = int(row.get("acc_rating")[1])
            stars_total = int(row.get("stars"))
            reviews_total = int(row.get("total_ratings"))

            ratings = ""

            if comm_total != 0:
                comm_avg = comm_good / comm_total
                if comm_avg >= 0.75:
                    ratings += f"`🟢 Communication ({comm_total})`\n"
                elif 0.5 <= comm_avg < 0.75:
                    ratings += f"`🟡 Communication ({comm_total})`\n"
                elif comm_avg < 0.5:
                    ratings += f"`🔴 Communication ({comm_total})`\n"
            if resp_total != 0:
                resp_avg = resp_good / resp_total
                if resp_avg >= 0.75:
                    ratings += f"`🟢 Responsiveness ({resp_total})`\n"
                elif 0.5 <= resp_avg < 0.75:
                    ratings += f"`🟡 Responsiveness ({resp_total})`\n"
                elif resp_avg < 0.5:
                    ratings += f"`🔴 Responsiveness ({resp_total})`\n"
            if pricing_total != 0:
                pricing_avg = pricing_good / pricing_total
                if pricing_avg >= 0.75:
                    ratings += f"`🟢 Fair Pricing ({pricing_total})`\n"
                elif 0.5 <= pricing_avg < 0.75:
                    ratings += f"`🟡 Fair Pricing ({pricing_total})`\n"
                elif pricing_avg < 0.5:
                    ratings += f"`🔴 Fair Pricing ({pricing_total})`\n"
            if ontime_total != 0:
                ontime_avg = ontime_good / ontime_total
                if ontime_avg >= 0.75:
                    ratings += f"`🟢 On-Time Meetup ({ontime_total})`\n"
                elif 0.5 <= ontime_avg < 0.75:
                    ratings += f"`🟡 On-Time Meetup ({ontime_total})`\n"
                elif ontime_avg < 0.5:
                    ratings += f"`🔴 On-Time Meetup ({ontime_total})`\n"
            if acc_total != 0:
                acc_avg = acc_good / acc_total
                if acc_avg >= 0.75:
                    ratings += f"`🟢 Accurate Description ({acc_total})`\n"
                elif 0.5 <= acc_avg < 0.75:
                    ratings += f"`🟡 Accurate Description ({acc_total})`\n"
                elif acc_avg < 0.5:
                    ratings += f"`🔴 Accurate Description ({acc_total})`\n"

            stars = ""
            if stars_total != 0:
                stars_avg = round((stars_total / reviews_total) * 2) / 2
                temp_stars = float(stars_avg)
                stars_emoji = ""
                for x in range(5):
                    if temp_stars > 0.5:
                        stars_emoji += " <:fullStarblack:999088726863007795> "
                    elif temp_stars > 0:
                        stars_emoji += " <:halfStar:999090417201070110> "
                    else:
                        stars_emoji += " <:hollowStar:999090418316754944> "
                    temp_stars -= 1
                stars = f"{stars_avg}/5 -{stars_emoji}"
            else:
                stars = "No ratings yet"

            embed.add_field("Overall Rating:", f"{stars} ({reviews_total})")
            if ratings != "":
                embed.add_field("Ratings:", ratings)

            # embed.set_footer(f"Joined: {joined_date}")
            embed.__setattr__("color", 0x000000)
        await conn.close()
        return embed


async def send_user_profile(author_id, user_id, guild_id, restApp: hikari.RESTApp, conn):
    BOT_TOKEN = os.getenv("BOT_TOKEN")
    async with restApp.acquire(BOT_TOKEN, hikari.TokenType.BOT) as bot_client:
        bot_client: hikari.impl.RESTClientImpl
        conn: asyncpg.Connection

        embed = await create_profile_embed(author_id, guild_id, restApp, conn)

        chnl = await bot_client.create_dm_channel(user_id)
        await chnl.send(embed=embed)
