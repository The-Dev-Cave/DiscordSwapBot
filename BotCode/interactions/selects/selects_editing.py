import asyncio
import itertools

import asyncpg
import flare
import hikari
import lightbulb

from BotCode.environment.database import get_database_connection

selects_plugin = lightbulb.Plugin("Editing Selects")


@flare.select(
    placeholder="Select 1 To Edit If Needed",
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
            value="payment methods",
            emoji=None,
            is_default=False,
        ),
    ],
    min_values=1,
    max_values=1,
)
async def edit_select_menu(ctx: flare.MessageContext, post_id: int = 0, post_type: str = "No Type",
                             guild_id: hikari.Snowflake = 123):
    print()


def load(bot: lightbulb.BotApp):
    bot.add_plugin(selects_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(selects_plugin)
