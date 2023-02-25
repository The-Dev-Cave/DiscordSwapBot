import flare
import hikari
import lightbulb

from BotCode.interactions.selects.selects_ratings import stars

buttons_ratings_plugin = lightbulb.Plugin("Database Functions", include_datastore=True)


class ButtonNoRating(flare.Button):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.DANGER
        self.label = "No"
        self.emoji = None
        self.disabled = False

    async def callback(self, ctx: flare.MessageContext) -> None:
        await ctx.message.edit(components=[])
        await ctx.respond("No rating will be submitted")


class ButtonStartRating(flare.Button):
    other_user_id: int
    post_type: str

    def __init__(self, other_user_id: int, post_type: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.style = hikari.ButtonStyle.SUCCESS
        self.label = "Yes"
        self.emoji = None
        self.disabled = False

        # custom attributes
        self.other_user_id = other_user_id
        self.post_type = post_type

    async def callback(self, ctx: flare.MessageContext) -> None:
        await ctx.message.edit(components=[])
        await ctx.respond(
            component=await flare.Row(
                stars(other_user_id=self.other_user_id, post_type=self.post_type)
            )
        )


def load(bot: lightbulb.BotApp):
    bot.add_plugin(buttons_ratings_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(buttons_ratings_plugin)
