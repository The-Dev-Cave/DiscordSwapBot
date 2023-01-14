import asyncio

import asyncpg
import flare
import hikari
import lightbulb

from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import create_profile_embed
from BotCode.interactions.modals import CreateProfileModal, ModalProfileDeny

buttons_profile_plugin = lightbulb.Plugin("Profile Buttons")


class ButtonCreateProfile(flare.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = kwargs.get("label")
        self.emoji = None
        self.disabled = False

        # custom attributes
        # self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext):
        await ctx.defer(
            flags=hikari.MessageFlag.EPHEMERAL,
            response_type=hikari.ResponseType.MESSAGE_CREATE,
        )
        conn = await get_database_connection()
        conn: asyncpg.Connection

        row = await conn.fetchrow(f'SELECT user_id from profiles where user_id={ctx.user.id}')
        if not row:
            await conn.execute(f'INSERT INTO profiles (user_id) values ({ctx.user.id})')

        data = (await conn.fetch(f'SELECT stage from profiles where user_id={ctx.user.id}'))[0]
        if int(data.get("stage")):
            await ctx.respond(
                "Your profile creation is already in progress or completed",
                flags=hikari.MessageFlag.EPHEMERAL,
            )
            await conn.close()
            return

        row = await flare.Row(ButtonStartProfile(label="Start Profile"))
        await conn.execute(f"UPDATE profiles set stage=1 where user_id={ctx.user.id}")
        await ctx.user.send(
            "Click the button below to open a popup to input some information",
            component=row,
        )
        await ctx.respond(
            "Please check your DMs to make your profile",
            flags=hikari.MessageFlag.EPHEMERAL,
        )
        await conn.close()


class ButtonStartProfile(flare.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = kwargs.get("label")
        self.emoji = None
        self.disabled = False

        # custom attributes
        # self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext):
        modal = CreateProfileModal()
        await modal.send(ctx.interaction)


class ButtonProfileFinish(flare.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = kwargs.get("label")
        self.emoji = None
        self.disabled = False

        # custom attributes
        # self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext):
        conn = await get_database_connection()
        conn: asyncpg.Connection
        await ctx.message.edit(components=[])
        user_id = ctx.user.id

        await conn.execute(f"UPDATE profiles set stage=4 where user_id={user_id}")

        embed = hikari.Embed(
            title="Profile Completed",
            description="Your profile is completed and to edit it, run `/profile edit {PartToEdit}`",
        )#.set_footer("This image will not be stored by the bot")

        await ctx.respond(embed=embed)
        await conn.close()


class ButtonProfileEdit(flare.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SECONDARY
        self.label = kwargs.get("label")
        self.emoji = None
        self.disabled = False

        # custom attributes
        # self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext):
        conn = await get_database_connection()
        conn: asyncpg.Connection

        user_id = ctx.user.id

        await conn.execute(f"UPDATE profiles set stage=1 where user_id={user_id}")
        await ctx.message.edit(components=[])
        row = await flare.Row(ButtonStartProfile(label="Edit Profile"))
        await ctx.user.send(
            "Click the button below to open a popup to input your info again",
            component=row,
        )
        await conn.close()


class ButtonSendToMods(flare.Button):
    guild_id: int
    def __init__(self, guild_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = kwargs.get("label")
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.guild_id = guild_id

    async def callback(self, ctx: flare.MessageContext):
        user_embed = hikari.Embed(
            title="Sent to mods for approval",
            description="You will be notified when approved or denied",
        )
        await ctx.respond(embed=user_embed)
        await ctx.message.edit(components=[])

        user_id = ctx.user.id

        conn = await get_database_connection()
        conn: asyncpg.Connection

        row = await conn.fetchrow(f"Select approval_channel_id from guilds where guild_id={self.guild_id}")

        profile_apprv_chnl = row.get(approval_channel_id)
        await conn.execute(f"UPDATE profiles set 'stage'=6 where 'user_id'={user_id}")

        # id_image_url = (
        #     await conn.fetch(f"SELECT 'tmp_img_url' from profiles where 'user_id'={user_id}")
        # )[0].get("id_image_url")

        btns_row = await flare.Row(
            ButtonProfileApprove(user_id=user_id, label="Approve"),
            ButtonProfileDeny(user_id=user_id, label="Deny"),
        )

        await ctx.bot.rest.create_message(
            profile_apprv_chnl,
            embed=(await create_profile_embed(user_id))
            .add_field(
                "Make sure everything is appropriate ",
                "If the profile looks good and follows Discord Terms Of Service and server rules, go ahead and approve, otherwise deny",
            ),
            component=btns_row,
        )
        await conn.close()


class ButtonProfileApprove(flare.Button):
    user_id: int

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = kwargs.get("label")
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.user_id = user_id

    async def callback(self, ctx: flare.MessageContext):
        user_id = self.user_id
        conn = await get_database_connection()
        conn: asyncpg.Connection

        await conn.execute(f"UPDATE profiles set 'stage'=7 where 'user_id'={user_id}")
        await ctx.message.delete()

        embed = hikari.Embed(
            title="Your profile has been approved",
            description="You now have access to make posts",
        )
        # await ctx.bot.rest.add_role_to_member(
        #     guild=ctx.guild_id, user=user_id, role=await get_verified_role_id()
        # )

        await ctx.bot.rest.create_message(
            channel=await ctx.bot.rest.create_dm_channel(user_id), embed=embed
        )
        row = await conn.fetchrow(f"Select 'Mod_Log_Channel_ID', 'Mod_Role_ID' from guilds where guild_id={ctx.guild_id}")
        await ctx.bot.rest.create_message(
            channel=row.get("Mod_Log_Channel_ID"),
            content=f"<@&{row.get('Mod_Role_ID')}>\n=============\n<@{user_id}> profile was created/approved",
            role_mentions=True,
            embed=await create_profile_embed(user_id),
        )
        await conn.close()


class ButtonProfileDeny(flare.Button):
    user_id: int

    def __init__(self, user_id, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = kwargs.get("label")
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.user_id = user_id

    async def callback(self, ctx: flare.MessageContext):
        await ctx.message.edit(
            component=await flare.Row(
                ButtonProfileDeny(user_id=self.user_id, label="Deny")
            )
        )
        msg = await ctx.message.respond(f"<@{self.user_id}> has denied this profile")
        modal = ModalProfileDeny(user_id=self.user_id, msg_id=msg.id)
        # modal = ModalProfileDeny()
        await modal.send(ctx.interaction)
        try:
            await asyncio.sleep(15)
            await msg.delete()
        except:
            pass


def load(bot: lightbulb.BotApp):
    bot.add_plugin(buttons_profile_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(buttons_profile_plugin)