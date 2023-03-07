import itertools

import hikari
import lightbulb
import flare

from BotCode.environment.database import get_database_connection
from BotCode.functions.send_logs import send_public_log
from BotCode.interactions.buttons.buttons_ratings import (
    ButtonNoRating,
    ButtonStartRating,
)

buttons_user_bridge_plugin = lightbulb.Plugin("User Bridge Buttons")


class ButtonMarkPostPending(flare.Button):
    post_id: int
    post_type: str
    post_owner_id: int

    def __init__(self, post_id, post_type, post_owner_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.PRIMARY
        self.label = "Mark As Pending"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.post_owner_id = post_owner_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        if ctx.user.id != self.post_owner_id:
            await ctx.respond(
                "You must be the lister to mark as pending",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            return
        conn = await get_database_connection()

        row = await conn.fetchrow(
            f"Select buy_channel_id,sell_channel_id,user_bridge_cat_id from guilds where guild_id={ctx.guild_id}"
        )
        swap_cat_id = row.get("user_bridge_cat_id")
        post_types_dict = {
            "sell": row.get("sell_channel_id"),
            "buy": row.get("buy_channel_id"),
        }
        try:

            row = await conn.fetchrow(
                f"Select message_id, post_status, title from {self.post_type} where id={self.post_id}"
            )
            pending = row.get("post_status")

            msg = await ctx.bot.rest.fetch_message(
                post_types_dict.get(self.post_type), row.get("message_id")
            )
        except:
            await ctx.respond(
                "Post no longer able to be marked as pending",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            await conn.close()
            return

        if (pending is None) or (int(pending) == int(0)):
            embed = msg.embeds[0]
            embed.__setattr__("color", 0xFF0000)
            embed.__setattr__("title", embed.__getattribute__("title") + " (Pending)")
            await msg.edit(embed=embed)
            await conn.execute(
                f"update {self.post_type} set post_status=1 where id={self.post_id}"
            )
            await ctx.respond(
                embed=hikari.Embed(
                    title="Post has been marked as **PENDING** ",
                    description="",
                    color=0xFFDD00,
                )
            )
            await send_public_log(
                guild_id=ctx.guild_id,
                text=f"**{self.post_type.upper()}:** <@{self.post_owner_id}> **UPDATED** listing __{row.get('title')}__ to **PENDING**",
            )

            channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)

            test2 = itertools.groupby(
                filter(
                    lambda c: isinstance(c[1], hikari.GuildTextChannel),
                    channels.items(),
                ),
                key=lambda c: c[1].parent_id,
            )
            for item in test2:
                cat_id = item[0]
                if cat_id == swap_cat_id:
                    for i in item[1]:
                        if (str(self.post_id) in str(i[1].name)) and (
                            str(i[0]) != str(ctx.channel_id)
                        ):
                            await ctx.bot.rest.create_message(
                                channel=i[0],
                                embed=hikari.Embed(
                                    title="Post has been marked as **PENDING** ",
                                    description="",
                                    color=0xFFDD00,
                                ),
                            )
                    break
        else:
            embed = msg.embeds[0]
            embed.__setattr__("color", 0xFFDD00)
            embed.__setattr__("title", row.get("title"))
            await msg.edit(embed=embed)
            await conn.execute(
                f"update {self.post_type} set post_status=0 where id={self.post_id}"
            )
            await ctx.respond(
                embed=hikari.Embed(
                    title="Post is marked as **AVAILABLE**",
                    description="",
                    color=0x00FF00,
                )
            )
            await send_public_log(
                guild_id=ctx.guild_id,
                text=f"**{self.post_type.upper()}:** <@{self.post_owner_id}> **UPDATED** listing __{row.get('title')}__ to **AVAILABLE**",
            )
            channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)

            test2 = itertools.groupby(
                filter(
                    lambda c: isinstance(c[1], hikari.GuildTextChannel),
                    channels.items(),
                ),
                key=lambda c: c[1].parent_id,
            )
            for item in test2:
                cat_id = item[0]
                if cat_id == swap_cat_id:
                    for i in item[1]:
                        if (str(self.post_id) in str(i[1].name)) and (
                            str(i[0]) != str(ctx.channel_id)
                        ):
                            await ctx.bot.rest.create_message(
                                channel=i[0],
                                embed=hikari.Embed(
                                    title="Post has been marked as **AVAILABLE**",
                                    description="",
                                    color=0x00FF00,
                                ),
                            )
                    break
        await conn.close()


class ButtonMarkPostSold(flare.Button):
    post_id: int
    post_type: str
    post_owner_id: int
    int_party_id: int

    def __init__(
        self, post_id, post_type, post_owner_id, int_party_id, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Mark As Sold"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.post_owner_id = post_owner_id
        self.int_party_id = int_party_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        if ctx.user.id != self.post_owner_id:
            await ctx.respond(
                "You must be the lister to mark as sold",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            return
        # async with get_database_connection() as conn:
        conn = await get_database_connection()
        post_done_dict = {"sell": "sold", "buy": "bought"}
        row = await conn.fetchrow(
            f"Select buy_channel_id,sell_channel_id,user_bridge_cat_id from guilds where guild_id={ctx.guild_id}"
        )
        post_types_dict = {
            "sell": row.get("sell_channel_id"),
            "buy": row.get("buy_channel_id"),
        }
        swap_cat_id = row.get("user_bridge_cat_id")

        row = await conn.fetchrow(
            f"Select message_id,title from {self.post_type} where id={self.post_id}"
        )
        try:

            post_snow = row.get("message_id")
            btn = await flare.Row(
                ButtonCloseUserBridge(
                    post_id=self.post_id,
                    post_type=self.post_type,
                    post_owner_id=self.post_owner_id,
                    int_party_id=self.int_party_id,
                )
            )
            await (
                await ctx.bot.rest.fetch_message(
                    message=post_snow,
                    channel=post_types_dict.get(self.post_type),
                )
            ).delete()
        except:

            await ctx.respond(
                embed=hikari.Embed(
                    title=f"Post been already marked as {post_done_dict.get(self.post_type)}",
                    description=f"Item is {post_done_dict.get(self.post_type)} so can't mark as {post_done_dict.get(self.post_type)} again",
                ),
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            await conn.close()
            return

        await ctx.respond(
            component=btn,
            embed=hikari.Embed(
                title=f"Item is marked as {post_done_dict.get(self.post_type)}",
                description=f"The post has been deleted from the <#{post_types_dict.get(self.post_type)}> channel.\nThe other channels connected have been deleted and this channel will be left open until you close it",
            ),
        )
        await send_public_log(
            guild_id=ctx.guild_id,
            text=f"**{self.post_type.upper()}:** <@{self.post_owner_id}> has **SOLD** listing __{row.get('title')}__",
        )
        channels = ctx.bot.cache.get_guild_channels_view_for_guild(ctx.guild_id)

        test2 = itertools.groupby(
            filter(
                lambda c: isinstance(c[1], hikari.GuildTextChannel), channels.items()
            ),
            key=lambda c: c[1].parent_id,
        )
        for item in test2:
            cat_id = item[0]
            if cat_id == swap_cat_id:
                for i in item[1]:
                    if (str(i[1].id) != str(ctx.channel_id)) and (
                        str(self.post_id) in str(i[1].name)
                    ):
                        await ctx.bot.rest.delete_channel(i[1].id)

        await conn.execute(f"delete from {self.post_type} where id={self.post_id}")

        int_party = await ctx.bot.rest.fetch_member(
            guild=ctx.guild_id, user=self.int_party_id
        )
        lister = await ctx.bot.rest.fetch_member(guild=ctx.guild_id, user=ctx.user.id)

        lister_prof = await conn.fetchrow(
            f"SELECT stage from profiles where user_id={ctx.user.id}"
        )
        if lister_prof and (int(lister_prof.get("stage")) == 3):
            embed = hikari.Embed(
                title=f"Would you like to rate {lister.display_name} from the completed transaction?",
                description="This is completely optional",
            )

            await ctx.bot.rest.create_message(
                await ctx.bot.rest.create_dm_channel(self.int_party_id),
                component=await flare.Row(
                    ButtonStartRating(
                        post_type=self.post_type, other_user_id=lister.id
                    ),
                    ButtonNoRating(),
                ),
                embed=embed,
            )

        int_party_prof = await conn.fetchrow(
            f"SELECT stage from profiles where user_id={self.int_party_id}"
        )
        if int_party_prof and (int(int_party_prof.get("stage")) == 3):
            embed = hikari.Embed(
                title=f"Would you like to rate {int_party.display_name} from the completed transaction?",
                description="This is completely optional",
            )
            await ctx.bot.rest.create_message(
                await ctx.bot.rest.create_dm_channel(self.post_owner_id),
                component=await flare.Row(
                    ButtonStartRating(
                        post_type=self.post_type, other_user_id=lister.id
                    ),
                    ButtonNoRating(),
                ),
                embed=embed,
            )
        await conn.close()


class ButtonCloseUserBridge(flare.Button):
    post_id: int
    post_type: str
    post_owner_id: int | hikari.Snowflake
    int_party_id: int

    def __init__(
        self, post_id, post_type, post_owner_id, int_party_id, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = "Close Channel"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type
        self.post_owner_id = post_owner_id
        self.int_party_id = int_party_id

    async def callback(self, ctx: flare.MessageContext) -> None:
        perm_overwrites = [
            hikari.PermissionOverwrite(
                type=hikari.PermissionOverwriteType.MEMBER,
                deny=(
                    hikari.Permissions.VIEW_CHANNEL
                    | hikari.Permissions.READ_MESSAGE_HISTORY
                    | hikari.Permissions.SEND_MESSAGES
                ),
                id=ctx.user.id,
            ),
            hikari.PermissionOverwrite(
                type=hikari.PermissionOverwriteType.MEMBER,
                deny=(
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
                ),
                id=buttons_user_bridge_plugin.bot.get_me().id,
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
        await ctx.get_channel().edit(permission_overwrites=perm_overwrites)

        await ctx.respond(
            embed=hikari.Embed(
                title="Channel Is Closed",
                description="It is safe to delete the channel",
            ),
            component=await flare.Row(delete_channel()),
        )


@flare.button(label="Delete Channel", style=hikari.ButtonStyle.DANGER)
async def delete_channel(ctx: flare.MessageContext) -> None:
    await ctx.get_channel().delete()


class ButtonShowMoreImages(flare.Button):
    post_id: int
    post_type: str

    def __init__(self, post_id, post_type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.PRIMARY
        self.label = "See More Images"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.post_id = post_id
        self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext) -> None:
        conn = await get_database_connection()
        row = await conn.fetchrow(
            f"SELECT add_images from {self.post_type} where id={self.post_id}"
        )
        response = "Click `dismiss message` at bottom of interaction to remove this message||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​||||​|| _ _ _ _ _ _\n"
        for i in row.get("add_images").split("|"):
            response += f"{i}\n"
        await ctx.respond(response, flags=hikari.MessageFlag.EPHEMERAL)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(buttons_user_bridge_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(buttons_user_bridge_plugin)
