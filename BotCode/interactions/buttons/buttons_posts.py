import asyncio
import itertools

import asyncpg
import flare
import hikari
import datetime

import lightbulb

from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import buildPostEmbed
from BotCode.functions.send_logs import send_mod_log, send_public_log
from BotCode.interactions.buttons.buttons_user_bridge import (
    ButtonMarkPostPending,
    ButtonMarkPostSold,
    ButtonCloseUserBridge,
    ButtonShowMoreImages,
)
from BotCode.interactions.modals import ModalPostSellBuyPart1, ModalPostDeny
from BotCode.interactions.selects.selects import update_post
from BotCode.interactions.selects.selects_editing import edit_select_menu

buttons_posts_plugin = lightbulb.Plugin("Posts Buttons")


class ButtonCreatePost(flare.Button):
    post_type: str
    guild_id: hikari.Snowflake

    def __init__(self, post_type, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.PRIMARY
        self.label = kwargs.get("label")
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_type = post_type
        self.guild_id = guild_id

    async def callback(self, ctx: flare.MessageContext):
        await ctx.defer(
            flags=hikari.MessageFlag.EPHEMERAL,
            response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE,
        )
        conn = await get_database_connection()
        conn: asyncpg.Connection

        post_type = self.post_type
        user_id = ctx.user.id

        types = {"sell": 1, "buy": 2}

        row = await conn.fetchrow(
            f"SELECT user_id from profiles where user_id={ctx.user.id}"
        )
        if not row:
            await conn.execute(f"INSERT INTO profiles (user_id) values ({ctx.user.id})")

        profile_required = await conn.fetchval(
            "SELECT profile_required from guilds where guild_id=$1", ctx.guild_id
        )
        profile_stage = await conn.fetchval(
            "SELECT stage from profiles where user_id=$1", ctx.user.id
        )
        if profile_required and (profile_stage != 4):
            await ctx.respond(
                "This guild requires a profile to be made. Please use </profile create:1234> to make your profile or go to https://swapbot.thedevcave.xyz",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            await conn.close()
            return

        making_post = (
            await conn.fetch(
                f"SELECT making_post from profiles where user_id={user_id}"
            )
        )[0].get("making_post")

        if making_post:
            await ctx.respond(
                "You have a post in progress. Cancel the current one or finish the one in progress to make a new post",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            await conn.close()
            return

        if post_type == "sell":
            await conn.execute(
                rf"INSERT into sell (author_id, stage, guild_id) values ({str(user_id)},1, {ctx.guild_id})"
            )
        else:
            await conn.execute(
                rf"INSERT into buy (author_id, guild_id) values ({str(user_id)}, {ctx.guild_id})"
            )

        post_id = (
            await conn.fetch(
                rf"SELECT id from {post_type} where (cast(author_id as bigint) = {user_id}) and ((pending_approval = FALSE) and (post_date IS NULL))"
            )
        )[0].get("id")

        embed = hikari.Embed(
            title="Part 1",
            description="Click 'Start Post' to open a popup to input some basic information",
        )

        embed.add_field(
            "Title",
            "Keep it short, simple, and concise. Add more specific details in the description. Also, to cancel your listing creation, come back and click the Cancel button at any time.",
            inline=True,
        )
        embed.add_field(
            "Description",
            "Ensure you include important and relevant details.",
            inline=True,
        )

        try:

            await ctx.user.send(
                embed=embed,
                component=await flare.Row(
                    ButtonPostPart1(
                        post_id=post_id, post_type=post_type, guild_id=ctx.guild_id
                    ),
                    ButtonCancel(post_id=post_id, post_type=post_type, label="Cancel"),
                ),
            )
        except:
            await ctx.respond(
                content="Please allow dms from users in this server",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            await conn.execute(
                rf"DELETE from {post_type} where (author_id in {str(user_id)}) and (stage = 1)"
            )
            await conn.execute(
                rf"UPDATE profiles set making_post=0 where user_id = {ctx.user.id}"
            )
            await conn.close()
            return

        await conn.execute(
            rf"UPDATE profiles set making_post={types[post_type]} WHERE user_id={user_id}"
        )

        await ctx.respond(
            "Please check your dms to get started", flags=hikari.MessageFlag.EPHEMERAL
        )
        await conn.close()


class ButtonCancel(flare.Button):
    # __slots__ = ("post_id", "post_type")
    post_id: int
    post_type: str

    def __init__(self, post_id, post_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = kwargs.get("label")
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext):
        await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
        conn = await get_database_connection()
        conn: asyncpg.Connection
        post_id = self.post_id
        post_type = self.post_type

        user_id = ctx.user.id

        await conn.execute(rf"DELETE from {post_type} where id = {post_id}")
        await conn.execute(
            rf"UPDATE profiles set making_post=0 where user_id = {user_id}"
        )

        await ctx.message.edit(components=None)
        embed = hikari.Embed(
            title="Post in progress has been cancelled",
            description=f"Go back to the guild start a new post",
        )
        await ctx.respond(embed=embed)
        await conn.close()


class ButtonPostPart1(flare.Button):
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake

    def __init__(
        self, post_id: int, post_type: str, guild_id: hikari.Snowflake, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Start Post"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.guild_id = guild_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        modal = ModalPostSellBuyPart1(
            post_type=self.post_type, post_id=self.post_id, guild_id=self.guild_id
        )

        if self.post_type == "trading":
            modal.append(
                flare.TextInput(
                    label="Looking For",
                    placeholder="Ex. Any item of similar value",
                    style=hikari.TextInputStyle.PARAGRAPH,
                )
            )
        else:
            modal.append(
                flare.TextInput(
                    label="Budget/Cost", placeholder="Ex. 10", max_length=10
                )
            )

        await modal.send(ctx.interaction)


class ButtonNoPhoto(flare.Button):
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake

    def __init__(self, post_id, post_type, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SECONDARY
        self.label = "No Photo"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.guild_id = guild_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        conn = await get_database_connection()
        conn: asyncpg.Connection
        await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_UPDATE)

        await conn.execute(
            f"UPDATE {self.post_type} set image='nophoto', stage=3 where id={self.post_id}"
        )
        await ctx.message.edit(components=[])
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
            await ctx.interaction.edit_initial_response(
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
            await ctx.interaction.edit_initial_response(
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

        await conn.close()


class ButtonSendPostToMods(flare.Button):
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake

    def __init__(self, post_id, post_type, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Finish Post"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.guild_id = guild_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
        conn = await get_database_connection()
        conn: asyncpg.Connection

        user_embed = hikari.Embed(
            title="Post sent to guild",
            description="Feel free to start making another post if you want. You do not need to wait for this post to be looked at by mods if approval is enabled",
        )
        await ctx.respond(embed=user_embed)

        post_embed = await buildPostEmbed(
            post_id=self.post_id, post_type=self.post_type, user=ctx.user
        )
        approve_channel = await conn.fetchval(
            f"Select approval_channel_id from guilds where guild_id={self.guild_id}"
        )

        await ctx.message.edit(components=[])

        post_approval: bool = await conn.fetchval(
            "SELECT post_approval from guilds where guild_id=$1", self.guild_id
        )

        await conn.execute(
            f"UPDATE {self.post_type} set pending_approval={post_approval} where id={self.post_id}"
        )
        row = None
        if self.post_type == "sell":
            row = await conn.fetchrow(
                f"SELECT add_images from {self.post_type} where id={self.post_id}"
            )

        if row and row.get("add_images"):
            btns_row = await flare.Row(
                ButtonShowMoreImages(post_id=self.post_id, post_type=self.post_type),
                ButtonApprovePost(post_id=self.post_id, post_type=self.post_type),
                ButtonDenyPost(post_id=self.post_id, post_type=self.post_type),
            )
        else:
            btns_row = await flare.Row(
                ButtonApprovePost(post_id=self.post_id, post_type=self.post_type),
                ButtonDenyPost(post_id=self.post_id, post_type=self.post_type),
            )

        if post_approval:
            await ctx.bot.rest.create_message(
                channel=approve_channel, embed=post_embed, component=btns_row
            )
        else:
            row = None
            if self.post_type == "sell":
                row = await conn.fetchrow(
                    f"SELECT author_id, title, add_images from {self.post_type} where id={self.post_id}"
                )
            else:
                row = await conn.fetchrow(
                    f"SELECT author_id, title from {self.post_type} where id={self.post_id}"
                )
            lister_id = row.get("author_id")
            post_title = row.get("title")
            user = await ctx.bot.rest.fetch_member(self.guild_id, lister_id)

            row_chan = await conn.fetchrow(
                f"Select buy_channel_id,sell_channel_id from guilds where guild_id={self.guild_id}"
            )

            post_types_dict = {
                "sell": row_chan.get("sell_channel_id"),
                "buy": row_chan.get("buy_channel_id"),
            }

            embed = await buildPostEmbed(
                post_id=self.post_id, post_type=self.post_type, user=user
            )

            if row.get("add_images"):
                btns_row = await flare.Row(
                    ButtonContactLister(
                        post_id=self.post_id,
                        post_type=self.post_type,
                        post_owner_id=user.id,
                        post_title=post_title,
                    ),
                    ButtonShowMoreImages(
                        post_id=self.post_id, post_type=self.post_type
                    ),
                    ButtonReportPost(
                        post_id=self.post_id,
                        post_type=self.post_type,
                        post_owner_id=user.id,
                    ),
                    ButtonUpdatePost(
                        post_id=self.post_id,
                        post_type=self.post_type,
                        post_owner_id=user.id,
                    ),
                )
            else:
                btns_row = await flare.Row(
                    ButtonContactLister(
                        post_id=self.post_id,
                        post_type=self.post_type,
                        post_owner_id=user.id,
                        post_title=post_title,
                    ),
                    ButtonReportPost(
                        post_id=self.post_id,
                        post_type=self.post_type,
                        post_owner_id=user.id,
                    ),
                    ButtonUpdatePost(
                        post_id=self.post_id,
                        post_type=self.post_type,
                        post_owner_id=user.id,
                    ),
                )

            created_message = await ctx.bot.rest.create_message(
                channel=post_types_dict[self.post_type], embed=embed, component=btns_row
            )

            await conn.execute(
                f"UPDATE {self.post_type} set pending_approval=FALSE, message_id={created_message.id}, post_date='{datetime.datetime.today()}' where id={self.post_id}"
            )
        await conn.execute(
            f"UPDATE profiles set making_post=0 where user_id={ctx.user.id}"
        )

        await conn.close()


class ButtonNewPostPhotos(flare.Button):
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake

    def __init__(self, post_id, post_type, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SECONDARY
        self.label = "New Photo(s)"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.guild_id = guild_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        await ctx.defer(response_type=hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
        conn = await get_database_connection()
        conn: asyncpg.Connection

        embed = hikari.Embed(
            title="Send the new photo(s) in one message",
            description="Try to post a photo that shows as much of the item as possible and is not blurry. You may add multiple photos at once to your message.  The first attached image will be the main one showed on the post",
            color=0xFFDD00,
        )
        await ctx.message.edit(components=[])
        msg = await (
            await ctx.respond(
                embed=embed,
                component=await flare.Row(
                    ButtonNoPhoto(
                        post_id=self.post_id,
                        post_type=self.post_type,
                        guild_id=self.guild_id,
                    ),
                    ButtonCancel(
                        post_id=self.post_id,
                        post_type=self.post_type,
                        label="Cancel Post",
                    ),
                ),
            )
        ).retrieve_message()
        await conn.execute(
            f"UPDATE sell set stage=2,image={msg.id} where id={self.post_id}"
        )
        await conn.close()


class ButtonApprovePost(flare.Button):
    post_id: int
    post_type: str

    def __init__(self, post_id, post_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Approve"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext) -> None:
        conn = await get_database_connection()
        conn: asyncpg.Connection

        await ctx.message.edit(components=[])

        row = None
        if self.post_type == "sell":
            row = await conn.fetchrow(
                f"SELECT author_id, title, add_images from {self.post_type} where id={self.post_id}"
            )
        else:
            row = await conn.fetchrow(
                f"SELECT author_id, title from {self.post_type} where id={self.post_id}"
            )
        lister_id = row.get("author_id")
        post_title = row.get("title")
        user = await ctx.bot.rest.fetch_member(ctx.guild_id, lister_id)

        row_chan = await conn.fetchrow(
            f"Select buy_channel_id,sell_channel_id from guilds where guild_id={ctx.guild_id}"
        )

        post_types_dict = {
            "sell": row_chan.get("sell_channel_id"),
            "buy": row_chan.get("buy_channel_id"),
        }

        embed = await buildPostEmbed(
            post_id=self.post_id, post_type=self.post_type, user=user
        )

        if row.get("add_images"):
            btns_row = await flare.Row(
                ButtonContactLister(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=user.id,
                    post_title=post_title,
                ),
                ButtonShowMoreImages(post_id=self.post_id, post_type=self.post_type),
                ButtonReportPost(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=user.id,
                ),
                ButtonUpdatePost(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=user.id,
                ),
            )
        else:
            btns_row = await flare.Row(
                ButtonContactLister(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=user.id,
                    post_title=post_title,
                ),
                ButtonReportPost(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=user.id,
                ),
                ButtonUpdatePost(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=user.id,
                ),
            )

        created_message = await ctx.bot.rest.create_message(
            channel=post_types_dict[self.post_type], embed=embed, component=btns_row
        )

        await conn.execute(
            f"UPDATE {self.post_type} set pending_approval=FALSE, message_id={created_message.id}, post_date='{datetime.datetime.today()}' where id={self.post_id}"
        )

        await ctx.message.delete()
        await send_mod_log(
            guild_id=ctx.guild_id,
            text=f"{ctx.author.mention} **({ctx.author.username}#{ctx.author.discriminator})** has **APPROVED** __{post_title}__",
        )
        await conn.close()


class ButtonDenyPost(flare.Button):
    post_id: int
    post_type: str

    def __init__(self, post_id, post_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = "Deny"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext) -> None:
        await ctx.message.edit(
            component=await flare.Row(
                ButtonDenyPost(post_id=self.post_id, post_type=self.post_type)
            )
        )
        modal = ModalPostDeny(post_type=self.post_type, post_id=self.post_id)
        await modal.send(ctx.interaction)


class ButtonContactLister(flare.Button):
    post_id: int
    post_type: str
    post_owner_id: int
    post_title: str

    def __init__(
        self, post_id, post_type, post_title, post_owner_id: int, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Contact"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.post_title = post_title
        self.post_owner_id = post_owner_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        if ctx.user.id == self.post_owner_id:
            await ctx.respond(
                "You can't create a chat channel with yourself",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            return

        await ctx.respond(
            "A chat channel is being created if not already exists.  You will be pinged in it when done",
            flags=hikari.MessageFlag.EPHEMERAL,
        )

        perm_overwrites = [
            hikari.PermissionOverwrite(
                type=hikari.PermissionOverwriteType.MEMBER,
                allow=(
                    hikari.Permissions.VIEW_CHANNEL
                    | hikari.Permissions.READ_MESSAGE_HISTORY
                    | hikari.Permissions.SEND_MESSAGES
                ),
                id=ctx.user.id,
            ),
            hikari.PermissionOverwrite(
                type=hikari.PermissionOverwriteType.MEMBER,
                allow=(
                    hikari.Permissions.VIEW_CHANNEL
                    | hikari.Permissions.READ_MESSAGE_HISTORY
                    | hikari.Permissions.SEND_MESSAGES
                ),
                id=self.post_owner_id,
            ),
            hikari.PermissionOverwrite(
                type=hikari.PermissionOverwriteType.MEMBER,
                allow=(
                    hikari.Permissions.VIEW_CHANNEL
                    | hikari.Permissions.READ_MESSAGE_HISTORY
                    | hikari.Permissions.SEND_MESSAGES
                ),
                id=buttons_posts_plugin.bot.get_me().id,
            ),
            hikari.PermissionOverwrite(
                type=hikari.PermissionOverwriteType.ROLE,
                deny=(
                    hikari.Permissions.VIEW_CHANNEL
                    | hikari.Permissions.READ_MESSAGE_HISTORY
                    | hikari.Permissions.SEND_MESSAGES
                ),
                id=ctx.guild_id,
            ),
        ]
        user_name = ctx.member.display_name
        msg_url = (
            await ctx.bot.rest.fetch_message(ctx.channel_id, ctx.message)
        ).make_link(ctx.guild_id)
        conn = await get_database_connection()

        channel_name = f"{user_name[0:10]}-{self.post_id}".replace(" ", "-").lower()

        channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)
        swap_cat_id = await conn.fetchval(
            f"Select user_bridge_cat_id from guilds where guild_id={ctx.guild_id}"
        )
        chnls_grouped = itertools.groupby(
            filter(
                lambda c: isinstance(c[1], hikari.GuildTextChannel),
                channels.items(),
            ),
            key=lambda c: c[1].parent_id,
        )
        for item in chnls_grouped:
            cat_id = item[0]
            if cat_id == swap_cat_id:
                for i in item[1]:
                    if str(i[1].name) == channel_name:
                        return
                break

        channel = await ctx.bot.rest.create_guild_text_channel(
            guild=ctx.guild_id,
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
        if self.post_type == "sell":
            row = await conn.fetchrow(
                f"SELECT add_images from {self.post_type} where id={self.post_id}"
            )
        if row and row.get("add_images"):
            btns_row = await flare.Row(
                ButtonShowMoreImages(post_id=self.post_id, post_type=self.post_type),
                ButtonMarkPostPending(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=self.post_owner_id,
                ),
                ButtonMarkPostSold(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=self.post_owner_id,
                    int_party_id=ctx.user.id,
                ),
                ButtonCloseUserBridge(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=self.post_owner_id,
                    int_party_id=ctx.user.id,
                ),
            )
        else:
            btns_row = await flare.Row(
                ButtonMarkPostPending(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=self.post_owner_id,
                ),
                ButtonMarkPostSold(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=self.post_owner_id,
                    int_party_id=ctx.user.id,
                ),
                ButtonCloseUserBridge(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=self.post_owner_id,
                    int_party_id=ctx.user.id,
                ),
            )

        await channel.send(embed=embed, component=btns_row)

        await channel.send(
            content=f"Listing: **{self.post_title}**\nLister: <@{self.post_owner_id}>\nInterested Party: {ctx.member.mention}",
            user_mentions=True,
        )
        await conn.close()
        try:
            await ctx.edit_response(f"Channel Link\n<#{channel.id}>")
        except:
            pass


# noinspection PyTypeChecker
class ButtonUpdatePost(flare.Button):
    post_id: int
    post_type: str
    post_owner_id: int

    def __init__(self, post_id, post_type, post_owner_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SECONDARY
        self.label = "EDIT"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.post_owner_id = post_owner_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        if ctx.user.id != self.post_owner_id:
            await ctx.respond(
                "You must be the post lister to update it",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            return

        await ctx.respond(
            content="To cancel click `dismiss message` at bottom of interaction",
            components=await asyncio.gather(
                flare.Row(update_post(post_id=self.post_id, post_type=self.post_type)),
            ),
            flags=hikari.MessageFlag.EPHEMERAL,
        )


class ButtonReportPost(flare.Button):
    post_id: int
    post_type: str
    post_owner_id: int

    def __init__(self, post_id, post_type, post_owner_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = "Report"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.post_owner_id = post_owner_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        # if ctx.user.id != self.post_owner_id:
        #     await ctx.respond("You must be the post lister to update it", flags=hikari.MessageFlag.EPHEMERAL)
        #     return

        await ctx.respond(
            content="Report sent to mods", flags=hikari.MessageFlag.EPHEMERAL
        )

        conn = await get_database_connection()
        row = await conn.fetchrow(
            f"SELECT * from {self.post_type} where id=$1", self.post_id
        )
        guild_data = await conn.fetchrow(
            "SELECT sell_channel_id, buy_channel_id,mod_role_id from guilds where guild_id=$1",
            ctx.guild_id,
        )

        channel = (
            guild_data.get("sell_channel_id")
            if self.post_type == "sell"
            else guild_data.get("buy_channel_id")
        )

        msg_url = (
            await ctx.bot.rest.fetch_message(ctx.channel_id, ctx.message)
        ).make_link(ctx.guild_id)

        # await send_mod_log(ctx.guild_id, f"{ctx.author.mention} ({ctx.author.username}#{ctx.author.discriminator}) has reported [{row.get('title')}]({msg_url})")
        await send_mod_log(
            ctx.guild_id,
            f"<@&{guild_data.get('mod_role_id')}>{ctx.author.mention} ({ctx.author.username}#{ctx.author.discriminator}) has reported **__{row.get('title')}__** in <#{channel}>",
        )


class ButtonEditNoPhoto(flare.Button):
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake

    def __init__(self, post_id, post_type, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SECONDARY
        self.label = "No Photo"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.guild_id = guild_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        await ctx.message.edit(components=[])
        await ctx.defer(hikari.ResponseType.DEFERRED_MESSAGE_CREATE)
        conn = await get_database_connection()
        post = await conn.fetchrow(
            f"SELECT message_id, author_id, title from sell where id={self.post_id}"
        )
        guild = await conn.fetchrow(
            f"SELECT sell_channel_id from guilds where guild_id={self.guild_id}"
        )

        await conn.execute(f"UPDATE sell set image='nophoto', add_images='', stage=3 where id={self.post_id}")
        await conn.execute(f"UPDATE profiles set making_post=0 where user_id={ctx.author.id}")
        await send_public_log(guild_id=self.guild_id, text=f"**{self.post_type.upper()}:** <@{post.get('author_id')}> **UPDATED** listing __{post.get('title')}__ to have **NO IMAGE(S)**")
        embed = await buildPostEmbed(
            post_id=self.post_id, post_type=self.post_type, user=ctx.author
        )
        btns_row = await flare.Row(
            ButtonContactLister(
                post_id=self.post_id,
                post_type=self.post_type,
                post_owner_id=ctx.author.id,
                post_title=post.get("title"),
            ),
            ButtonReportPost(
                post_id=self.post_id,
                post_type=self.post_type,
                post_owner_id=ctx.author.id,
            ),
            ButtonUpdatePost(
                post_id=self.post_id,
                post_type=self.post_type,
                post_owner_id=ctx.author.id,
            ),
        )
        await buttons_posts_plugin.bot.rest.edit_message(
            channel=guild.get("sell_channel_id"),
            message=post.get("message_id"),
            embed=embed,
            component=btns_row
        )
        await ctx.respond("Post has been edited to have no images")


def load(bot: lightbulb.BotApp):
    bot.add_plugin(buttons_posts_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(buttons_posts_plugin)
