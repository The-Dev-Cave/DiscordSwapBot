import asyncio
import asyncpg
import flare
import hikari
import datetime

import lightbulb

from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import buildPostEmbed
from BotCode.interactions.buttons.buttons_user_bridge import ButtonMarkPostPending, ButtonMarkPostSold, \
    ButtonCloseUserBridge, ButtonShowMoreImages
from BotCode.interactions.modals import ModalPostSellBuyPart1, ModalPostDeny
from BotCode.interactions.selects.selects import update_post

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
            response_type=hikari.ResponseType.MESSAGE_CREATE,
        )
        conn = await get_database_connection()
        conn: asyncpg.Connection

        post_type = self.post_type
        user_id = ctx.user.id

        types = {"sell": 1, "buy": 2}

        making_post = (
            await conn.fetch(f"SELECT making_post from profiles where user_id={user_id}")
        )[0].get("making_post")


        if making_post:
            await ctx.respond(
                "You have a post in progress. Cancel the current one or finish the one in progress to make a new post",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            await conn.close()
            return

        await conn.execute(
            rf"INSERT into {post_type} (author_id, stage, guild_id) values ({str(user_id)},1, {ctx.guild_id})"
        )
        post_id = (
            await conn.fetch(
                rf"SELECT id from {post_type} where (cast(author_id as bigint) = {user_id}) and (stage = 1)"
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
                    ButtonPostPart1(post_id=post_id, post_type=post_type, guild_id=ctx.guild_id),
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
                rf"UPDATE profiles set making_post=0 where 'user_id' = {ctx.user.id}"
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
        conn = await get_database_connection()
        conn: asyncpg.Connection
        post_id = self.post_id
        post_type = self.post_type

        user_id = ctx.user.id

        await conn.execute(rf"DELETE from {post_type} where id = {post_id}")
        await conn.execute(rf"UPDATE profiles set making_post=0 where user_id = {user_id}")

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

    def __init__(self, post_id: int, post_type: str, guild_id: hikari.Snowflake, *args, **kwargs):
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
        modal = ModalPostSellBuyPart1(post_type=self.post_type, post_id=self.post_id, guild_id=self.guild_id)

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
                flare.TextInput(label="Cost/Budget", placeholder="Ex. 10")
            )

        await modal.send(ctx.interaction)


class ButtonNoPhoto(flare.Button):
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake

    def __init__(self, post_id, post_type, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
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

        await conn.execute(
            f"UPDATE {self.post_type} set image='nophoto' where id={self.post_id}"
        )
        await ctx.message.edit(components=[])
        embed = await buildPostEmbed(
            post_id=self.post_id, post_type=self.post_type, user=ctx.user
        )

        btns_row = await flare.Row(
            ButtonSendPostToMods(post_id=self.post_id, post_type=self.post_type, guild_id=self.guild_id),
            ButtonNewPostPhotos(post_id=self.post_id, post_type=self.post_type, guild_id=self.guild_id),
        )
        await ctx.respond(embed=embed, component=btns_row)
        # add send buttons
        # await ctx.respond(embed=embed)

        await conn.close()


class ButtonSendPostToMods(flare.Button):
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake

    def __init__(self, post_id, post_type, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Send Post For Approval"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.guild_id = guild_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        conn = await get_database_connection()
        conn: asyncpg.Connection

        user_embed = hikari.Embed(
            title="Post sent to mods for approval",
            description="Feel free to start making another post if you want. You do not need to wait for this post to be looked at by mods",
        )
        await ctx.respond(embed=user_embed)

        post_embed = await buildPostEmbed(
            post_id=self.post_id, post_type=self.post_type, user=ctx.user
        )
        approve_channel = await conn.fetchval(f"Select approval_channel_id from guilds where guild_id={self.guild_id}")

        await ctx.message.edit(components=[])

        await conn.execute(
            f"UPDATE {self.post_type} set pending_approval=TRUE where id={self.post_id}"
        )

        row = await conn.fetchrow(f"SELECT add_images from {self.post_type} where id={self.post_id}")

        if row.get("add_images"):
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

        await ctx.bot.rest.create_message(
            channel=approve_channel, embed=post_embed, component=btns_row
        )
        await conn.execute(f"UPDATE profiles set making_post=0 where user_id={ctx.user.id}")

        await conn.close()


class ButtonNewPostPhotos(flare.Button):
    post_id: int
    post_type: str
    guild_id: hikari.Snowflake
    def __init__(self, post_id, post_type, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = "New Photo(s)"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.guild_id = guild_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        conn = await get_database_connection()
        conn: asyncpg.Connection

        await conn.execute(
            f"UPDATE {self.post_type} set stage=2 where id={self.post_id}"
        )
        embed = hikari.Embed(
            title="Send the new photo(s) in one message",
            description="Try to post a photo that shows as much of the item as possible and is not blurry. You may add multiple photos at once to your message.  The first attached image will be the main one showed on the post",
            color=0xFFDD00,
        )
        await ctx.message.edit(components=[])
        await ctx.respond(
            embed=embed,
            component=await flare.Row(
                ButtonNoPhoto(post_id=self.post_id, post_type=self.post_type, guild_id=self.guild_id)
            ),
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

        row = (await conn.fetchrow(f"SELECT author_id, title, add_images from {self.post_type} where id={self.post_id}"))
        lister_id = row.get("author_id")
        post_title = row.get("title")
        user = await ctx.bot.rest.fetch_member(ctx.guild_id, lister_id)

        row_chan = await conn.fetchrow(
            f"Select buy_channel_id,sell_channel_id from guilds where guild_id={ctx.guild_id}")

        post_types_dict = {"sell": row_chan.get('sell_channel_id'), "buy": row_chan.get('buy_channel_id')}

        embed = await buildPostEmbed(post_id=self.post_id, post_type=self.post_type, user=user)

        if row.get("add_images"):
            btns_row = await flare.Row(
                ButtonShowMoreImages(post_id=self.post_id, post_type=self.post_type),
                ButtonContactLister(post_id=self.post_id, post_type=self.post_type, post_owner_id=user.id,
                                    post_title=post_title),
                ButtonUpdatePost(post_id=self.post_id, post_type=self.post_type, post_owner_id=user.id)
            )
        else:
            btns_row = await flare.Row(
                ButtonContactLister(post_id=self.post_id, post_type=self.post_type, post_owner_id=user.id,
                                    post_title=post_title),
                ButtonUpdatePost(post_id=self.post_id, post_type=self.post_type, post_owner_id=user.id)
            )

        created_message = await ctx.bot.rest.create_message(channel=post_types_dict[self.post_type], embed=embed,
                                                            component=btns_row)

        await conn.execute(
            f"UPDATE {self.post_type} set pending_approval=FALSE, message_id={created_message.id}, post_date='{datetime.datetime.today()}' where id={self.post_id}")

        await ctx.message.delete()
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

    def __init__(self, post_id, post_type, post_title, post_owner_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Contact Lister"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.post_title = post_title
        self.post_owner_id = post_owner_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        if ctx.user.id == self.post_owner_id:
            await ctx.respond("You can't create a chat channel with yourself", flags=hikari.MessageFlag.EPHEMERAL)
            return

        await ctx.respond("A chat channel is being created.  You will be pinged in it when done",
                          flags=hikari.MessageFlag.EPHEMERAL)
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
            )
        ]
        user_name = ctx.member.display_name.split(" ")
        msg_url = (
            await ctx.bot.rest.fetch_message(
                ctx.channel_id, ctx.message
            )
        ).make_link(ctx.guild_id)
        channel_name = f"{user_name[0][0]}{user_name[1]}-{self.post_id}"

        conn = await get_database_connection()
        swap_cat_id = await conn.fetchval(f"Select 'User_Bridge_cat_ID' from guilds where guild_id={ctx.guild_id}")

        channel = await ctx.bot.rest.create_guild_text_channel(guild=ctx.guild_id,
                                                               name=channel_name,
                                                               permission_overwrites=perm_overwrites,
                                                               category=swap_cat_id)
        embed = hikari.Embed(title="Welcome to the user bridge!",
                             description=f"Only the lister can mark as pending or sold and neither will close the channel\nMarking as sold will close other channels connect to this post\nRun `/viewprofile user` to see basic info about the other person and their photo for identification\n[Link to Original Post]({msg_url})",
                             color=0x00FF00,
                             url=msg_url)
        row = await conn.fetchrow(f"SELECT add_images from {self.post_type} where id={self.post_id}")
        if row.get("add_images"):
            btns_row = await flare.Row(ButtonShowMoreImages(post_id=self.post_id, post_type=self.post_type),
                                       ButtonMarkPostPending(post_id=self.post_id, post_type=self.post_type,
                                                             post_owner_id=self.post_owner_id),
                                       ButtonMarkPostSold(post_id=self.post_id, post_type=self.post_type,
                                                          post_owner_id=self.post_owner_id, int_party_id=ctx.user.id),
                                       ButtonCloseUserBridge(post_id=self.post_id, post_type=self.post_type,
                                                             post_owner_id=self.post_owner_id, int_party_id=ctx.user.id)
                                       )
        else:
            btns_row = await flare.Row(
                                       ButtonMarkPostPending(post_id=self.post_id, post_type=self.post_type,
                                                             post_owner_id=self.post_owner_id),
                                       ButtonMarkPostSold(post_id=self.post_id, post_type=self.post_type,
                                                          post_owner_id=self.post_owner_id, int_party_id=ctx.user.id),
                                       ButtonCloseUserBridge(post_id=self.post_id, post_type=self.post_type,
                                                             post_owner_id=self.post_owner_id, int_party_id=ctx.user.id)
                                       )

        await channel.send(embed=embed, component=btns_row)

        # add buttons for marking as sold and pending
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
        self.style = hikari.ButtonStyle.DANGER
        self.label = "Update Post"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.post_owner_id = post_owner_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        if ctx.user.id != self.post_owner_id:
            await ctx.respond("You must be the post lister to update it", flags=hikari.MessageFlag.EPHEMERAL)
            return

        await ctx.respond(
            content="To cancel click `dismiss message` at bottom of interaction",
            components=await asyncio.gather(
                flare.Row(update_post(post_id=self.post_id, post_type=self.post_type)),
            ),
            flags=hikari.MessageFlag.EPHEMERAL
        )


def load(bot: lightbulb.BotApp):
    bot.add_plugin(buttons_posts_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(buttons_posts_plugin)