import datetime
import re
import croniter
import flare
from lightbulb.ext import tasks
import lightbulb
import hikari

from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import buildPostEmbed
from BotCode.interactions.buttons.buttons_posts import (
    ButtonContactLister,
    ButtonUpdatePost,
    ButtonReportPost,
)
from BotCode.interactions.buttons.buttons_user_bridge import ButtonShowMoreImages

expired_PL = lightbulb.Plugin("statusUpdater")


# @tasks.task(s=20, auto_start=True, wait_before_execution=True)
@tasks.task(tasks.CronTrigger("59 14 * * *"), auto_start=True)
async def expired():
    # print("task ran")
    conn = await get_database_connection()

    rows = []
    today = datetime.date.today()

    for table in ["sell", "buy"]:
        row = await conn.fetch(
            f"Select id,post_date,author_id,title,message_id,renew_count,guild_id from {table} where notified_expiry is FALSE and message_id is not null"
        )
        rows.append(row)

    i = 0
    curr_guild_id = None
    expiry = 7
    renew_count = 3
    for item in rows:
        post_type = ""
        if i == 0:
            table = "sell"
            post_type = "sell"
        elif i == 1:
            table = "buy"
            post_type = "buy"
        # elif i == 2:
        #     table = "Trading"
        #     post_type = "trading"
        i = i + 1
        for row in item:
            post_id = row.get("id")
            posted_at = row.get("post_date")
            user_id = row.get("author_id")
            title = row.get("title")
            post_snow = row.get("message_id")
            expires = row.get("renew_count")
            guild_id = row.get("guild_id")
            if str(guild_id) != str(curr_guild_id):
                curr_guild_id = guild_id
                guild_row = await conn.fetchrow(
                    "SELECT expiry_time,renewal_count from guilds where guild_id=$1",
                    guild_id,
                )
                expiry = guild_row.get("expiry_time")
                renew_count = guild_row.get("renewal_count")
            user = await expired_PL.bot.rest.fetch_user(user_id)
            if posted_at is None:
                continue
            delta = (today - posted_at).days
            if delta >= expiry:
                await conn.execute(
                    f"update {table} set renew_count={expires + 1},notified_expiry=TRUE where id={post_id}"
                )
                btns = await flare.Row(
                    ButtonRepost(post_id=post_id, post_type=post_type),
                    ButtonNoRepost(post_id=post_id, post_type=post_type),
                )

                row_chnls = await conn.fetchrow(
                    "SELECT buy_channel_id,sell_channel_id from guilds where guild_id=$1",
                    guild_id,
                )

                match post_type:
                    # Try catch, error out ping mods
                    # Ask if mods want to repost then notify user if no repost with reason
                    case "sell":
                        await expired_PL.bot.rest.delete_message(
                            row_chnls.get("sell_channel_id"), post_snow
                        )
                    case "buy":
                        await expired_PL.bot.rest.delete_message(
                            row_chnls.get("buy_channel_id"), post_snow
                        )
                    # case "trading":
                    #     await expired_PL.bot.rest.delete_message(
                    #         await get_trd_post_chn_id(), post_snow
                    #     )
                if expires < renew_count:
                    await user.send(
                        embed=hikari.Embed(
                            title=f"{title} - Post has expired, repost?",
                            description="Clicking yes will repost for another 7 days without any edits",
                        ),
                        component=btns,
                    )
                else:
                    await conn.execute(f"delete from {table} where id={post_id}")
                    await user.send(
                        embed=hikari.Embed(
                            title=f"{title} - Post has expired",
                            description="You have reposted 3 times. Remake the post to post again",
                        )
                    )
    await conn.close()


class ButtonRepost(flare.Button):
    post_id: int
    post_type: str

    def __init__(self, post_id, post_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Yes"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext) -> None:
        await ctx.message.edit(components=[])
        embed = hikari.Embed(
            title="Would you like to update price/budget?",
            description="Click yes to open a popup to input an new number or no to repost with no change",
        )

        btns = await flare.Row(
            ButtonChangePrice(post_id=self.post_id, post_type=self.post_type),
            ButtonDontChangePrice(post_id=self.post_id, post_type=self.post_type),
        )

        await ctx.respond(embed=embed, component=btns)


class ButtonNoRepost(flare.Button):
    post_id: int
    post_type: str

    def __init__(self, post_id, post_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = "No"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext) -> None:
        await ctx.message.edit(components=[])
        conn = await get_database_connection()

        title = await conn.fetchval(
            f"SELECT title from {self.post_type} where id={self.post_id}"
        )

        await ctx.respond(
            embed=hikari.Embed(
                title=f"Your {title} post will not be reposted",
                description="You will need to make a new post to post it again",
            )
        )
        await conn.execute(f"delete from {self.post_type} where id={self.post_id}")
        await conn.close()


class ButtonChangePrice(flare.Button):
    post_id: int
    post_type: str

    def __init__(self, post_id, post_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Yes"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext) -> None:
        modal = ModalNewCost(post_id=self.post_id, post_type=self.post_type)

        await modal.send(ctx.interaction)


class ButtonDontChangePrice(flare.Button):
    post_id: int
    post_type: str

    def __init__(self, post_id, post_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = "No"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext) -> None:
        conn = await get_database_connection()
        post = None
        if self.post_type == "sell":
            post = await conn.fetchrow(
                f"SELECT title,author_id,guild_id,add_images from sell where id={self.post_id}"
            )
        else:
            post = await conn.fetchrow(
                f"SELECT title,author_id,guild_id from buy where id={self.post_id}"
            )
        await ctx.message.edit(components=[])
        await ctx.respond(
            embed=hikari.Embed(
                title=f"Your {post.get('title')} post is being reposted",
                description="It will be like a brand new post",
            )
        )
        lister = int(post.get("author_id"))
        post_title = post.get("title")
        # btns_row = await flare.Row(
        #     ButtonContactLister(post_id=self.post_id, post_type=self.post_type, post_owner_id=lister, post_title=post_title),
        #     ButtonUpdatePost(post_id=self.post_id, post_type=self.post_type, post_owner_id=lister)
        # )
        if post.get("add_images"):
            btns_row = await flare.Row(
                ButtonContactLister(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=lister,
                    post_title=post_title,
                ),
                ButtonShowMoreImages(post_id=self.post_id, post_type=self.post_type),
                ButtonReportPost(
                    post_id=self.post_id, post_type=self.post_type, post_owner_id=lister
                ),
                ButtonUpdatePost(
                    post_id=self.post_id, post_type=self.post_type, post_owner_id=lister
                ),
            )
        else:
            btns_row = await flare.Row(
                ButtonContactLister(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=lister,
                    post_title=post_title,
                ),
                ButtonReportPost(
                    post_id=self.post_id, post_type=self.post_type, post_owner_id=lister
                ),
                ButtonUpdatePost(
                    post_id=self.post_id, post_type=self.post_type, post_owner_id=lister
                ),
            )

        row_chnls = await conn.fetchrow(
            "SELECT buy_channel_id,sell_channel_id from guilds where guild_id=$1",
            post.get("guild_id"),
        )
        post_types_channel_dict = {
            "buy": row_chnls.get("buy_channel_id"),
            "sell": row_chnls.get("sell_channel_id"),
        }
        msg = await ctx.bot.rest.create_message(
            post_types_channel_dict.get(self.post_type),
            embed=await buildPostEmbed(
                post_id=self.post_id, post_type=self.post_type, user=ctx.user
            ),
            component=btns_row,
        )
        await conn.execute(
            f"update {self.post_type} set notified_expiry=FALSE,message_id={msg.id},post_date='{datetime.datetime.today()}' where id={self.post_id}"
        )
        await conn.close()


class ModalNewCost(flare.Modal, title="New Post Cost/Budget"):
    post_id: int
    post_type: str

    text_input_cost: flare.TextInput = flare.TextInput(
        label="New Cost",
        placeholder="Ex. '10' or '9.50'",
        style=hikari.TextInputStyle.SHORT,
        max_length=10,
    )

    async def callback(self, ctx: flare.ModalContext) -> None:

        user_input = self.text_input_cost.value

        if (
            not (user_input.isdigit() or user_input.replace(".", "", 1).isdigit())
        ) or user_input.__contains__("-"):
            await ctx.respond(
                hikari.Embed(
                    title="Not a valid cost input",
                    description="Must be an integer or decimal",
                )
            )
            return
        if user_input.replace(".", "", 1).isdigit():
            user_input = round(float(user_input), 2)
        else:
            user_input = int(user_input)

        conn = await get_database_connection()

        await conn.execute(
            rf"UPDATE {self.post_type} set price=ROUND(CAST('{user_input}' AS NUMERIC), 2) where id={self.post_id}"
        )

        post = None
        if self.post_type == "sell":
            post = await conn.fetchrow(
                f"SELECT title,author_id,guild_id,add_images from sell where id={self.post_id}"
            )
        else:
            post = await conn.fetchrow(
                f"SELECT title,author_id,guild_id from buy where id={self.post_id}"
            )
        await ctx.interaction.message.edit(components=[])
        await ctx.respond(
            embed=hikari.Embed(
                title=f"Your {post.get('title')} post is being reposted",
                description="It will be like a brand new post",
            )
        )
        lister = int(post.get("author_id"))
        post_title = post.get("title")
        # btns_row = await flare.Row(
        #     ButtonContactLister(post_id=self.post_id, post_type=self.post_type, post_owner_id=lister, post_title=post_title),
        #     ButtonUpdatePost(post_id=self.post_id, post_type=self.post_type, post_owner_id=lister)
        # )
        if post.get("add_images"):
            btns_row = await flare.Row(
                ButtonContactLister(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=lister,
                    post_title=post_title,
                ),
                ButtonShowMoreImages(post_id=self.post_id, post_type=self.post_type),
                ButtonReportPost(
                    post_id=self.post_id, post_type=self.post_type, post_owner_id=lister
                ),
                ButtonUpdatePost(
                    post_id=self.post_id, post_type=self.post_type, post_owner_id=lister
                ),
            )
        else:
            btns_row = await flare.Row(
                ButtonContactLister(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=lister,
                    post_title=post_title,
                ),
                ButtonReportPost(
                    post_id=self.post_id, post_type=self.post_type, post_owner_id=lister
                ),
                ButtonUpdatePost(
                    post_id=self.post_id, post_type=self.post_type, post_owner_id=lister
                ),
            )

        row_chnls = await conn.fetchrow(
            "SELECT buy_channel_id,sell_channel_id from guilds where guild_id=$1",
            post.get("guild_id"),
        )
        post_types_channel_dict = {
            "buy": row_chnls.get("buy_channel_id"),
            "sell": row_chnls.get("sell_channel_id"),
        }
        msg = await ctx.bot.rest.create_message(
            post_types_channel_dict.get(self.post_type),
            embed=await buildPostEmbed(
                post_id=self.post_id, post_type=self.post_type, user=ctx.user
            ),
            component=btns_row,
        )
        await conn.execute(
            f"update {self.post_type} set notified_expiry=FALSE,message_id={msg.id},post_date='{datetime.datetime.today()}' where id={self.post_id}"
        )
        await conn.close()


def load(bot: lightbulb.BotApp):
    bot.add_plugin(expired_PL)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(expired_PL)
