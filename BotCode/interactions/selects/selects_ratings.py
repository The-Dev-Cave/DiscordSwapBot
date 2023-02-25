import asyncio

import flare
import hikari
import lightbulb

from BotCode.environment.database import get_database_connection

selects_ratings_plugin = lightbulb.Plugin("User Bridge Buttons")


@flare.select(
    placeholder="Overall Rating /5 Stars",
    options=[
        hikari.SelectMenuOption(
            label="1 Star", value="1", description="", emoji=None, is_default=False
        ),
        hikari.SelectMenuOption(
            label="2 Star", value="2", description="", emoji=None, is_default=False
        ),
        hikari.SelectMenuOption(
            label="3 Star", value="3", description="", emoji=None, is_default=False
        ),
        hikari.SelectMenuOption(
            label="4 Star", value="4", description="", emoji=None, is_default=False
        ),
        hikari.SelectMenuOption(
            label="5 Star", value="5", description="", emoji=None, is_default=False
        ),
    ],
)
async def stars(ctx: flare.MessageContext, other_user_id: int, post_type: str):
    embed = hikari.Embed(
        title=f"Overall Rating Set: {ctx.values[0]} star(s)",
        description="Next: Select what was good about the transaction that relates to the transaction type",
    )
    embed.add_field("Communication", "The overall communication was pretty good")
    embed.add_field("Responsiveness", "The overall responsiveness was pretty good")
    embed.add_field("Fair Pricing", "The pricing was fair/reasonable")
    embed.add_field("On Time", "When meeting up, they were on time")
    embed.add_field(
        "Item As Described",
        "Description of item was accurate or item was better than described",
    )
    await ctx.respond(
        embed=embed,
        components=await asyncio.gather(
            flare.Row(
                good_menu(
                    other_user_id=other_user_id,
                    post_type=post_type,
                    star_rat=int(ctx.values[0]),
                )
            ),
        ),
    )
    await ctx.message.edit(components=[])


@flare.select(
    placeholder="Select What Was Good",
    options=[
        hikari.SelectMenuOption(
            label="None", value="none", description="", emoji=None, is_default=False
        ),
        hikari.SelectMenuOption(
            label="Communication",
            value="comm",
            description="",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Responsiveness",
            value="resp",
            description="",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Fair Pricing",
            value="pric",
            description="",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="On Time", value="time", description="", emoji=None, is_default=False
        ),
        hikari.SelectMenuOption(
            label="Item As Described",
            value="desc",
            description="",
            emoji=None,
            is_default=False,
        ),
    ],
    min_values=1,
    max_values=5,
)
async def good_menu(
    ctx: flare.MessageContext, other_user_id: int, post_type: str, star_rat: int
):
    await ctx.message.edit(components=[])
    selected = ""
    for item in ctx.values:
        selected += f"{item}\n"
    embed = hikari.Embed(title=f"Good Options Selected", description=f"{selected}\n")
    embed.add_field("Next", "Select what was bad about the transaction if anything")
    embed.add_field("Communication", "The overall communication was pretty good")
    embed.add_field("Responsiveness", "The overall responsiveness was pretty good")
    embed.add_field("Fair Pricing", "The pricing was fair/reasonable")
    embed.add_field("On Time", "When meeting up, they were on time")
    embed.add_field(
        "Item As Described",
        "Description of item was accurate or item was better than described",
    )
    values = ""
    for val in ctx.values:
        values += f"{val}|"
    await ctx.respond(
        embed=embed,
        components=await asyncio.gather(
            flare.Row(
                bad_menu(
                    other_user_id=other_user_id,
                    post_type=post_type,
                    star_rat=star_rat,
                    good_rat=values,
                )
            ),
        ),
    )


@flare.select(
    placeholder="Select What Was Bad",
    options=[
        hikari.SelectMenuOption(
            label="None", value="none", description="", emoji=None, is_default=False
        ),
        hikari.SelectMenuOption(
            label="Communication",
            value="comm",
            description="",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Responsiveness",
            value="resp",
            description="",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="Fair Pricing",
            value="pric",
            description="",
            emoji=None,
            is_default=False,
        ),
        hikari.SelectMenuOption(
            label="On Time", value="time", description="", emoji=None, is_default=False
        ),
        hikari.SelectMenuOption(
            label="Item As Described",
            value="desc",
            description="",
            emoji=None,
            is_default=False,
        ),
    ],
    min_values=1,
    max_values=5,
)
async def bad_menu(
    ctx: flare.MessageContext,
    other_user_id: int,
    post_type: str,
    star_rat: int,
    good_rat: str,
):
    selected = ""
    for item in ctx.values:
        selected += f"{item}\n"
    embed = hikari.Embed(title=f"Bad Options Selected", description=f"{selected}\n")
    embed.add_field("Rating Submitted", "Rating has been submitted")
    await ctx.respond(embed=embed)
    await ctx.message.edit(components=[])
    conn = await get_database_connection()
    statement = ""
    good_rat = good_rat.split("|")
    if good_rat.count("none") < 1:
        for item in good_rat:
            match item:
                case "comm":
                    statement += "commGood= commGood+1, commTotal = commTotal+1, "
                case "resp":
                    statement += "respGood= respGood+1, respTotal = respTotal+1, "
                case "pric":
                    statement += (
                        "pricingGood= pricingGood+1, pricingTotal = pricingTotal+1, "
                    )
                case "time":
                    statement += (
                        "ontimeGood= ontimeGood+1, ontimeTotal = ontimeTotal+1, "
                    )
                case "desc":
                    statement += "accGood= accGood+1, accTotal = accTotal+1, "
    statement = statement[:-2]
    if ctx.values.count("none") < 1:
        for item in ctx.values:
            match item:
                case "comm":
                    if "comm" not in good_rat:
                        statement += ", commTotal = commTotal+1 "
                case "resp":
                    if "resp" not in good_rat:
                        statement += ", respTotal = respTotal+1 "
                case "pric":
                    if "pric" not in good_rat:
                        statement += ", pricingTotal = pricingTotal+1 "
                case "time":
                    if "time" not in good_rat:
                        statement += ", ontimeTotal = ontimeTotal+1 "
                case "desc":
                    if "desc" not in good_rat:
                        statement += ", accTotal = accTotal+1 "

    if len(statement) < 5:
        await conn.close()
        return
    await conn.execute(
        f"update profiles set {statement}, 'stars'='stars'+{star_rat}, 'total_ratings'='total_ratings'+1 where user_id = {other_user_id}"
    )
    await conn.close()


def load(bot: lightbulb.BotApp):
    bot.add_plugin(selects_ratings_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(selects_ratings_plugin)
