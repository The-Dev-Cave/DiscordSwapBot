import asyncio

import asyncpg
import flare
import hikari
import lightbulb

from BotCode.functions.send_logs import send_mod_log
from BotCode.interactions.selects.selects import condition_select_menu
from BotCode.environment.database import get_database_connection

modals_plugin = lightbulb.Plugin("Modals Functions")

class CreateProfileModal(flare.Modal, title="Profile Part 1"):
    text_input_fname: flare.TextInput = flare.TextInput(
        label="First Name", placeholder="First Name"
    )
    text_input_lname: flare.TextInput = flare.TextInput(
        label="Last Name", placeholder="Last Name"
    )
    text_input_pronouns: flare.TextInput = flare.TextInput(
        label=r"Pronouns-Ex. He/Him, She/Her, They/Them",
        placeholder="Can also do 'Prefer Not To Say'",
    )

    async def callback(self, ctx: flare.ModalContext) -> None:
        conn = await get_database_connection()
        conn: asyncpg.Connection

        fname = self.text_input_fname.value.title()
        lname = self.text_input_lname.value.title()
        pronouns = self.text_input_pronouns.value.title()

        await ctx.interaction.message.edit(
            components=[],
            content=f"First Name: {fname}\nLast Name: {lname}\nPronouns: {pronouns}",
        )

        embed = hikari.Embed(
                        title="Send an image that you want to use for your user profile for others to identify you",
                        description="Please have face easily visible and should show shoulders and up. Only one person in the photo.\n It will only be viewable when someone runs the `/viewprofile` command and it IS NOT changing your avatar/pfp for the server itself.",
                    )
        await ctx.respond(embed=embed)
        await conn.execute(
            f"UPDATE profiles set first_name='{fname}', last_name='{lname}', pronouns='{pronouns}', stage=2 where user_id={ctx.user.id}"
        )

        await conn.close()


class ModalProfileDeny(flare.Modal, title="Profile Deny"):
    user_id: int
    msg_id: int

    text_input_reason: flare.TextInput = flare.TextInput(
        label="Reason For Denial",
        placeholder="Reason",
        style=hikari.TextInputStyle.PARAGRAPH,
    )

    async def callback(self, ctx: flare.ModalContext) -> None:
        conn = await get_database_connection()
        conn: asyncpg.Connection

        reason = self.text_input_reason.value

        user_id = int(self.user_id)
        await conn.execute(f"UPDATE profiles set stage=0 where user_id={user_id}")

        embed = hikari.Embed(title="Profile Denied", description=f"Reason:\n {reason}")
        embed.set_footer(
            "You can remake your profile by clicking the button again in the verify channel"
        )
        await (await ctx.bot.rest.create_dm_channel(user_id)).send(embed=embed)

        await ctx.interaction.message.delete()
        await ctx.bot.rest.delete_message(ctx.channel_id, self.msg_id)

        await ctx.respond(
            "User has been notified of denial", flags=hikari.MessageFlag.EPHEMERAL
        )

        # row = await conn.fetchval("Select approval_channel_id")
        #
        # await ctx.bot.rest.create_message(
        #     channel=await get_name_log_chan_id(),
        #     content=f"<@{user_id}> profile has been denied",
        # )

        await conn.close()


# noinspection DuplicatedCode,PyTypeChecker
class ModalPostSellBuyPart1(flare.Modal, title="Profile Deny"):
    # user_id: int
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake

    text_input_title: flare.TextInput = flare.TextInput(
        label="Title", placeholder="Keep it short, simple, and concise.", style=hikari.TextInputStyle.SHORT
    )
    text_input_description: flare.TextInput = flare.TextInput(
        label="Description", placeholder="Include important and relevant details.", style=hikari.TextInputStyle.PARAGRAPH
    )

    async def callback(self, ctx: flare.ModalContext) -> None:
        from BotCode.interactions.buttons.buttons_posts import ButtonCancel

        conn = await get_database_connection()
        conn: asyncpg.Connection

        title = self.text_input_title.value.title()
        description = self.text_input_description.value
        third_input = ctx.values[2]

        embed = hikari.Embed(
            title="Received Values", description="The following is what was received"
        )
        embed.add_field("Title", f"{title}")
        embed.add_field("Description", f"{description}")

        valid_ptypes = ["sell", "buy"]
        if any(self.post_type == ptype for ptype in valid_ptypes):
            cost: int | float = 0
            if (
                not (third_input.isdigit() or third_input.replace(".", "", 1).isdigit())
            ) or third_input.__contains__("-"):
                await ctx.respond(
                    hikari.Embed(
                        title="Not a valid cost input",
                        description="Must be an integer or decimal",
                    )
                )
                return
            if third_input.replace(".", "", 1).isdigit():
                cost = round(float(third_input), 2)
            else:
                cost = int(third_input)
            await ctx.interaction.message.edit(
                components=[]
            )
            embed.add_field("Cost or Budget", f"{cost}")

            await conn.execute(
                rf"UPDATE {self.post_type} set title='{title}',description='{description}',price='{cost}' where id={self.post_id}"
            )

        else:
            embed.add_field("Looking For", f"{ctx.values[2]}")
            await conn.execute(
                rf"UPDATE {self.post_type} set title='{title}',description='{description}',looking_for='{third_input}' where id={self.post_id}"
            )
            await ctx.interaction.message.edit(
                component=await flare.Row(
                    ButtonCancel(
                        post_id=self.post_id, post_type=self.post_type, label="Cancel"
                    )
                )
            )

        embedNextStep = hikari.Embed(
            title="Item Condition",
            description="Select the item's condition if selling or worse condition you would buy\n",

            color=0xFFDD00,
        )
        await ctx.respond(
            embeds=[embed, embedNextStep],
            components=await asyncio.gather(
                flare.Row(
                    condition_select_menu(
                        post_id=self.post_id, post_type=self.post_type, guild_id=self.guild_id
                    )
                ), flare.Row(
                    ButtonCancel(post_id=self.post_id, post_type=self.post_type, label="Cancel")
                )
            ),
        )


class ModalPostDeny(flare.Modal, title="Profile Deny"):
    # msg_id: int
    post_type: str
    post_id: int

    text_input_reason: flare.TextInput = flare.TextInput(
        label="Reason For Denial",
        placeholder="Reason",
        style=hikari.TextInputStyle.PARAGRAPH,
    )

    async def callback(self, ctx: flare.ModalContext) -> None:
        conn = await get_database_connection()
        conn: asyncpg.Connection

        reason = self.text_input_reason.value

        post_id = int(self.post_id)

        post = await conn.fetchrow(
            f"SELECT title, author_id from {self.post_type} where id = {post_id}"
        )

        user_id = post.get("author_id")

        await conn.execute(f"DELETE from {self.post_type} where id={post_id}")

        embed = hikari.Embed(
            title=rf"Post '{post.get('title')}' Denied",
            description=f"Reason:\n {reason}\n\n\nGo back to the guild to start a new post addressing why the post denied",
        )
        await (await ctx.bot.rest.create_dm_channel(user_id)).send(embed=embed)

        await ctx.interaction.message.delete()
        # await ctx.bot.rest.delete_message(ctx.channel_id, self.msg_id)

        await ctx.respond(
            "User has been notified of denial", flags=hikari.MessageFlag.EPHEMERAL
        )
        await send_mod_log(guild_id=ctx.guild_id,
                           text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has **DENIED** __{post.get('title')}__ for reason:\n```{reason}```")

        await conn.close()


class ModalProfileChangeDeny(flare.Modal, title="Profile Update Deny"):
    profile_id: int

    text_input_reason: flare.TextInput = flare.TextInput(
        label="Reason For Denial",
        placeholder="Reason",
        style=hikari.TextInputStyle.PARAGRAPH,
    )

    async def callback(self, ctx: flare.ModalContext) -> None:
        conn = await get_database_connection()
        conn: asyncpg.Connection

        reason = self.text_input_reason.value

        profile_id = int(self.profile_id)

        embed = hikari.Embed(
            title=rf"Profile Change Denied",
            description=f"Reason:\n {reason}",
        )
        await (await ctx.bot.rest.create_dm_channel(profile_id)).send(embed=embed)

        await ctx.interaction.message.delete()

        await ctx.respond(
            "User has been notified of denial", flags=hikari.MessageFlag.EPHEMERAL
        )

        await conn.close()


def load(bot: lightbulb.BotApp):
    bot.add_plugin(modals_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(modals_plugin)