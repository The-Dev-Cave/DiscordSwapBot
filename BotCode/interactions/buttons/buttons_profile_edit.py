import flare
import hikari
import lightbulb

from BotCode.environment.database import get_database_connection
from BotCode.interactions.modals import ModalProfileChangeDeny

buttons_profile_edit_plugin = lightbulb.Plugin("Profile Edit Buttons")

class ButtonApproveChange(flare.Button):
    prof_id: int
    change_type: str
    change_to: str

    def __init__(self, prof_id: int, change_type: str, change_to: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Approve"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.prof_id = prof_id
        self.change_type = change_type
        self.change_to = change_to

    async def callback(self, ctx: flare.MessageContext):
        conn = await get_database_connection()
        msg=""
        if self.change_type == "lname":
            await conn.execute(f"UPDATE profiles set {self.change_type}='{self.change_to}' where 'user_id'={self.prof_id}")
            member = await ctx.bot.rest.fetch_member(guild=ctx.guild_id, user=self.prof_id)
            new_name = f"{member.display_name.split(' ')[0]} {self.change_to}"
            msg = "Your profile update for `Last Name` has been approved"
            await ctx.bot.rest.edit_member(guild=ctx.guild_id, user=self.prof_id, nickname=new_name)
        elif self.change_type == "profile_image_url":
            await conn.execute(f"UPDATE profiles set 'Profile_Picture'='id_image_url' where 'user_id'={self.prof_id}")
            msg = "Your profile update for `Profile Image` has been approved"

        await ctx.respond("User profile change approved", flags=hikari.MessageFlag.EPHEMERAL)

        await (await ctx.bot.rest.create_dm_channel(self.prof_id)).send(content=msg)
        await ctx.message.delete()
        await conn.close()


class ButtonDenyChange(flare.Button):
    prof_id: int

    def __init__(self, prof_id: int, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = "Deny"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.prof_id = prof_id

    async def callback(self, ctx: flare.MessageContext):
        modal = ModalProfileChangeDeny(profile_id=self.prof_id)
        await modal.send(ctx.interaction)


def load(bot: lightbulb.BotApp):
    bot.add_plugin(buttons_profile_edit_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(buttons_profile_edit_plugin)