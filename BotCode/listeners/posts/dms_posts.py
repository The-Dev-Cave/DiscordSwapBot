import asyncpg
import flare
import lightbulb
import hikari

from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import buildPostEmbed
from BotCode.interactions.buttons.buttons_posts import (
    ButtonSendPostToMods,
    ButtonNewPostPhotos,
)
from BotCode.interactions.buttons.buttons_user_bridge import ButtonShowMoreImages

posts_dms_plugin = lightbulb.Plugin("Lightbulb Bot Events")


@posts_dms_plugin.listener(event=hikari.DMMessageCreateEvent)
async def posts_dm(event: hikari.DMMessageCreateEvent):
    if event.is_bot:
        return
    conn = await get_database_connection()
    conn: asyncpg.Connection

    types = {1: "sell", 2: "buy"}

    post_type_int = (
        await conn.fetchrow(
            f"SELECT making_post from profiles where user_id={event.author.id}"
        )
    ).get("making_post")

    if not post_type_int:
        await conn.close()
        return

    post_type = types.get(post_type_int)

    post = await conn.fetchrow(
        f"SELECT id, stage, guild_id from {post_type} where author_id='{event.author.id}' and pending_approval is FALSE"
    )
    guild_id = post.get("guild_id")

    stage = post.get("stage")

    post_id = post.get("id")

    valid_stages = [2]
    if not any(stage == num for num in valid_stages):
        await conn.close()
        return

    try:
        first_img = event.message.attachments[0]
        print(
            f"Image for {post_type} post",
            first_img.media_type,
            first_img.filename,
        )
        if "image" not in first_img.media_type:
            await event.author.send("Please send an image file that discord recognizes")
            await conn.close()
            return

        img_urls = ""
        for image in event.message.attachments[1:4]:
            if "image" in image.media_type:
                img_urls += f"{image.url}|"

        await conn.execute(
            f"UPDATE {post_type} set stage=3,image='{first_img.url}',add_images='{img_urls}' where id={post_id}"
        )
        embed = await buildPostEmbed(
            post_id=post_id, post_type=post_type, user=event.author
        )
        btns_row = None
        if (len(event.message.attachments) > 1) and (img_urls != ""):
            btns_row = await flare.Row(
                ButtonSendPostToMods(post_id=post_id, post_type=post_type, guild_id=guild_id),
                ButtonNewPostPhotos(post_id=post_id, post_type=post_type, guild_id=guild_id),
                ButtonShowMoreImages(post_id=post_id, post_type=post_type)
            )
        else:
            btns_row = await flare.Row(
                ButtonSendPostToMods(post_id=post_id, post_type=post_type, guild_id=guild_id),
                ButtonNewPostPhotos(post_id=post_id, post_type=post_type, guild_id=guild_id),
            )
        await event.author.send(embed=embed, component=btns_row)
        await conn.close()

    except:
        await event.author.send("No file attached")
        await conn.close()

    # add send buttons


def load(bot: lightbulb.BotApp):
    bot.add_plugin(posts_dms_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(posts_dms_plugin)
