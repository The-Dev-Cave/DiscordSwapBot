import asyncio

import asyncpg
import flare
import lightbulb
import hikari

from BotCode.interactions.buttons.buttons_profile import (
    ButtonProfileFinish,
    ButtonProfileEdit,
    ButtonSendToMods,
)
from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import create_profile_embed

profile_listener_plugin = lightbulb.Plugin("Lightbulb Bot Events")


@profile_listener_plugin.listener(event=hikari.DMMessageCreateEvent)
async def dm_message_event(event: hikari.DMMessageCreateEvent):
    if event.author.is_bot:
        return
    conn = await get_database_connection()
    conn: asyncpg.Connection

    stage = (
        await conn.fetch(f"SELECT stage from profiles where user_id={event.author.id}")
    )[0].get("stage")

    valid_stages = [2, 4]
    if not any(stage == num for num in valid_stages):
        await conn.close()
        return

    try:
        image = event.message.attachments[0]
        print(
            "Image trying to set profile/id picture",
            image.media_type,
            image.filename,
        )
        if "image" not in image.media_type:
            await event.author.send("Please send an image file that discord recognizes")
            await conn.close()
            return
        if stage == 2:
            await conn.execute(
                f"UPDATE profiles set profile_picture='{image.url}' where user_id={event.author.id}"
            )
            await asyncio.sleep(0.5)
            embed = await create_profile_embed(event.author.id)
            await conn.execute(
                f"UPDATE profiles set stage=3 where user_id={event.author.id}"
            )

            chn = event.channel_id

            btns_row = await flare.Row(
                ButtonProfileEdit(label="Edit Profile"),
                ButtonProfileFinish(label="Finish Profile"),
            )

            await event.app.rest.create_message(
                content="**Here is what your profile looks like.**",
                channel=chn,
                embed=embed,
                component=btns_row,
            )

            # await event.author.send(
            #     content="The next step is to send an image of a School ID so we can confirm your name and profile image"
            # )

            # elif stage == 4:
            #     await conn.execute(
            #         f"UPDATE profiles set stage=5, tmp_img_url='{image.url}' where user_id={event.author.id}"
            #     )
            #     await asyncio.sleep(0.5)
            #     embed = hikari.Embed(
            #         title="ID Photo",
            #         description="Click 'Send' if the photo shows enough of your ID (At least photo of self and name)\n"
            #         "Or click 'New Photo' to upload a different photo",
            #     )
            #     embed.set_image(image.url)
            #     btns_row = await flare.Row(
            #         ButtonSendToMods(label="Send"),
            #         ButtonProfileSendID(label="New ID Photo"),
            #     )
            #
            #     await event.author.send(embed=embed, component=btns_row)
            await conn.close()
            return
    except:
        await event.author.send("No file attached")
        await conn.close()


def load(bot: lightbulb.BotApp):
    bot.add_plugin(profile_listener_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(profile_listener_plugin)
