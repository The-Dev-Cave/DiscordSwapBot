import asyncio

import asyncpg
import flare
import hikari
import lightbulb

from BotCode.functions.embeds import buildPostEmbed
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
class ModalPostSellBuyPart1(flare.Modal, title="Part 1"):
    # user_id: int
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake

    text_input_title: flare.TextInput = flare.TextInput(
        label="Title",
        placeholder="Keep it short, simple, and concise.",
        style=hikari.TextInputStyle.SHORT,
        max_length=30,
    )
    text_input_description: flare.TextInput = flare.TextInput(
        label="Description",
        placeholder="Include important and relevant details.",
        style=hikari.TextInputStyle.PARAGRAPH,
    )

    async def callback(self, ctx: flare.ModalContext) -> None:
        from BotCode.interactions.buttons.buttons_posts import ButtonCancel

        await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
        conn = await get_database_connection()
        conn: asyncpg.Connection

        title = self.text_input_title.value
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
            await ctx.interaction.message.edit(components=[])
            embed.add_field("Cost or Budget", f"{cost}")

            await conn.execute(
                rf"UPDATE {self.post_type} set title='{title}',description='{description}',price=ROUND(CAST('{cost}' AS NUMERIC), 2) where id={self.post_id}"
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
                        post_id=self.post_id,
                        post_type=self.post_type,
                        guild_id=self.guild_id,
                    )
                ),
                flare.Row(
                    ButtonCancel(
                        post_id=self.post_id, post_type=self.post_type, label="Cancel"
                    )
                ),
            ),
        )


class ModalPostDeny(flare.Modal, title="Post Deny"):
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
        await send_mod_log(
            guild_id=ctx.guild_id,
            text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has **DENIED** __{post.get('title')}__ for reason:\n```{reason}```",
        )

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


class ModalPostEdit(flare.Modal, title="Post Edit"):
    post_id: int
    post_type: str
    guild_id: int | hikari.Snowflakeish
    edit_option: str

    async def callback(self, ctx: flare.ModalContext) -> None:
        from BotCode.interactions.buttons.buttons_posts import (
            ButtonSendPostToMods,
            ButtonCancel,
            ButtonNewPostPhotos,
            ButtonShowMoreImages,
        )
        from BotCode.interactions.selects.selects_editing import edit_select_menu

        # await ctx.respond(flags=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
        user_input = ctx.values[0]

        # if self.edit_option in ['title']:
        #     self.edit_option = self.edit_option.title()

        if self.edit_option in ["price"]:
            cost: int | float = 0
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

        await ctx.interaction.message.edit(components=[])

        await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)

        conn = await get_database_connection()
        conn: asyncpg.Connection
        # await conn.execute("UPDATE $1 set $2=$3 where id=$4", self.post_type, self.edit_option, user_input, self.post_id)
        await conn.execute(
            f"UPDATE {self.post_type} set {self.edit_option}=$1 where id={self.post_id}",
            user_input,
        )
        embed = await buildPostEmbed(
            post_id=self.post_id, post_type=self.post_type, user=ctx.user
        )

        has_add_imgs = False
        if self.post_type == "sell":
            add_imgs = await conn.fetchval(
                f"SELECT add_images from sell where id={self.post_id}"
            )
            if add_imgs and (len(add_imgs) > 0):
                has_add_imgs = True

        if has_add_imgs:
            await modals_plugin.bot.rest.create_message(ctx.channel_id,
                # response_type=hikari.ResponseType.MESSAGE_CREATE,
                embed=embed,
                components=await asyncio.gather(
                    flare.Row(
                        edit_select_menu(
                            post_id=self.post_id,
                            post_type=self.post_type,
                            guild_id=self.guild_id,
                        )
                    ),
                    flare.Row(
                        ButtonSendPostToMods(
                            post_id=self.post_id,
                            post_type=self.post_type,
                            guild_id=self.guild_id,
                        ),
                        ButtonNewPostPhotos(
                            post_id=self.post_id,
                            post_type=self.post_type,
                            guild_id=self.guild_id,
                        ),
                        ButtonShowMoreImages(
                            post_id=self.post_id, post_type=self.post_type
                        ),
                        ButtonCancel(
                            post_id=self.post_id,
                            post_type=self.post_type,
                            label="Cancel",
                        ),
                    ),
                ),
            )
        else:
            if self.post_type == "sell":
                await modals_plugin.bot.rest.create_message(ctx.channel_id,
                    embed=embed,
                    components=await asyncio.gather(
                        flare.Row(
                            edit_select_menu(
                                post_id=self.post_id,
                                post_type=self.post_type,
                                guild_id=self.guild_id,
                            )
                        ),
                        flare.Row(
                            ButtonSendPostToMods(
                                post_id=self.post_id,
                                post_type=self.post_type,
                                guild_id=self.guild_id,
                            ),
                            ButtonNewPostPhotos(
                                post_id=self.post_id,
                                post_type=self.post_type,
                                guild_id=self.guild_id,
                            ),
                            ButtonCancel(
                                post_id=self.post_id,
                                post_type=self.post_type,
                                label="Cancel",
                            ),
                        ),
                    ),
                )
            else:
                await modals_plugin.bot.rest.create_message(ctx.channel_id,
                    embed=embed,
                    components=await asyncio.gather(
                        flare.Row(
                            edit_select_menu(
                                post_id=self.post_id,
                                post_type=self.post_type,
                                guild_id=self.guild_id,
                            )
                        ),
                        flare.Row(
                            ButtonSendPostToMods(
                                post_id=self.post_id,
                                post_type=self.post_type,
                                guild_id=self.guild_id,
                            ),
                            ButtonCancel(
                                post_id=self.post_id,
                                post_type=self.post_type,
                                label="Cancel",
                            ),
                        ),
                    ),
                )


class ModalPostEditAfterFinish(flare.Modal, title="Post Sent Edit"):
    post_id: int
    post_type: str
    guild_id: int | hikari.Snowflakeish
    edit_option: str

    async def callback(self, ctx: flare.ModalContext) -> None:
        from BotCode.functions.send_logs import send_public_log

        user_input = ctx.values[0]
        conn = await get_database_connection()

        if self.edit_option in ["price"]:
            cost: int | float = 0
            if (
                not (user_input.isdigit() or user_input.replace(".", "", 1).isdigit())
            ) or user_input.__contains__("-"):
                await ctx.edit_response(
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
        old_title = ""
        if self.edit_option == "title":
            old_title = await conn.fetchval(
                f"SELECT title from {self.post_type} where id={self.post_id}"
            )
        await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_UPDATE)
        await ctx.edit_response(
            components=[],
            content="Post is being edited. Free to dismiss message",
            embeds=[],
        )
        conn: asyncpg.Connection
        # await conn.execute("UPDATE $1 set $2=$3 where id=$4", self.post_type, self.edit_option, user_input, self.post_id)
        await conn.execute(
            f"UPDATE {self.post_type} set {self.edit_option}=$1 where id={self.post_id}",
            user_input,
        )

        guild = await conn.fetchrow(
            f"SELECT buy_channel_id, sell_channel_id from guilds where guild_id={self.guild_id}"
        )
        post = await conn.fetchrow(
            f"SELECT message_id, author_id, title from {self.post_type} where id={self.post_id}"
        )

        embed = await buildPostEmbed(
            post_id=self.post_id, post_type=self.post_type, user=ctx.user
        )

        chnl_dict = {
            "sell": guild.get("sell_channel_id"),
            "buy": guild.get("buy_channel_id"),
        }

        msg = await modals_plugin.bot.rest.fetch_message(
            channel=chnl_dict.get(self.post_type), message=post.get("message_id")
        )
        await msg.edit(embeds=[embed], attachments=None)

        if old_title:
            await send_public_log(
                self.guild_id,
                f"**{self.post_type.upper()}:** <@{post.get('author_id')}> **UPDATED** listing __{old_title}__ with a new **{self.edit_option.upper()}** to __{post.get('title')}__",
            )
        else:
            await send_public_log(
                self.guild_id,
                f"**{self.post_type.upper()}:** <@{post.get('author_id')}> **UPDATED** listing __{post.get('title')}__ with a new **{self.edit_option.upper()}**",
            )


def load(bot: lightbulb.BotApp):
    bot.add_plugin(modals_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(modals_plugin)
