import hikari
import lightbulb
import asyncpg
import datetime as DT

from BotCode.environment.database import get_database_connection

embeds_plugin = lightbulb.Plugin("Make Embeds")


async def create_profile_embed(
    userID: hikari.Snowflake | int, guild_id: hikari.Snowflake | int = None
) -> hikari.Embed:
    conn = await get_database_connection()
    conn: asyncpg.Connection

    data = (await conn.fetch(f"SELECT * from profiles where user_id='{userID}'"))[0]

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
        user = await embeds_plugin.bot.rest.fetch_user(userID)
        embed = hikari.Embed(
            title=f"{user.username}#{user.discriminator} Ratings",
            description="==================",
        )
        embed.set_thumbnail(user.display_avatar_url)

    if show_ratings:
        row = (await conn.fetch(f"SELECT * FROM profiles where user_id = {userID}"))[0]
        comm_good = int(row.get("commgood"))
        comm_total = int(row.get("commtotal"))
        resp_good = int(row.get("respgood"))
        resp_total = int(row.get("resptotal"))
        pricing_good = int(row.get("pricinggood"))
        pricing_total = int(row.get("pricingtoal"))
        ontime_good = int(row.get("ontimegood"))
        ontime_total = int(row.get("ontimetotal"))
        acc_good = int(row.get("accgood"))
        acc_total = int(row.get("acctotal"))
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


async def buildPostEmbed(post_id: int, post_type: str, user: hikari.User):
    conn = await get_database_connection()
    conn: asyncpg.Connection

    post_data = (await conn.fetch(f"SELECT * FROM {post_type} where id={post_id}"))[0]

    looking_for = None
    price = None

    title = post_data.get("title")
    description = post_data.get("description")
    pay_meth = post_data.get("payment_methods")
    img_link = post_data.get("image")
    if post_type == "trading":
        looking_for = post_data.get("looking_for")
    else:
        # print(post_data.get('price'))
        # print(round(post_data.get("price"), 2))
        price = round(post_data.get("price"), 2)
        # price.removesuffix(".0")
    condition = post_data.get("condition")
    # location = post_data.get("location")
    meetup = post_data.get("meetup")

    user_data = await conn.fetchrow(
        f"SELECT first_name, last_name from profiles where user_id={user.id}"
    )
    name = f'{user_data.get("first_name")} {user_data.get("last_name")}'
    embed = hikari.Embed(title=title, description=description).set_author(
        name=name, icon=user.avatar_url
    )

    if img_link != "nophoto":
        embed.set_image(img_link)

    if post_type == "buy":
        embed.add_field("Will Buy Condition Or Better", f"{condition}")
    else:
        embed.add_field("Item Condition", condition)

    if post_type == "trading":
        embed.add_field("Looking For", looking_for)
    else:
        if post_type == "buy":
            embed.add_field("Willing To Pay", f"${price}")
        else:
            embed.add_field("Item Price", f"${price}")

        embed.add_field("Lister's Preferred Payment Methods", pay_meth)

    # embed.add_field("Lister's Location", location)
    embed.add_field("Item Transaction", meetup)
    embed.set_footer(
        f"Expires: {(DT.datetime.today() + DT.timedelta(days=7)).strftime('%m-%d-%Y')} | [{post_id}]"
    )
    embed.__setattr__("color", 0xFFDD00)
    await conn.close()
    return embed


def load(bot):
    bot.add_plugin(embeds_plugin)


def unload(bot):
    bot.remove_plugin(embeds_plugin)
