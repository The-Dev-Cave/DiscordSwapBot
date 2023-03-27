import asyncio

import asyncpg
import flare
import lightbulb
import hikari

from BotCode.environment.database import get_database_connection
from BotCode.functions.embeds import buildPostEmbed
from BotCode.functions.send_logs import send_public_log
from BotCode.interactions.buttons.buttons_posts import (
    ButtonSendPostToMods,
    ButtonNewPostPhotos,
    ButtonCancel,
    ButtonContactLister,
    ButtonUpdatePost,
    ButtonReportPost,
)
from BotCode.interactions.buttons.buttons_user_bridge import ButtonShowMoreImages
from BotCode.interactions.selects.selects_editing import edit_select_menu

posts_dms_plugin = lightbulb.Plugin("Lightbulb Bot Events")


@posts_dms_plugin.listener(event=hikari.DMMessageCreateEvent)
async def posts_dm(event: hikari.DMMessageCreateEvent):
    if event.is_bot:
        return
    conn = await get_database_connection()
    conn: asyncpg.Connection
    types = {1: "sell", 2: "buy", 3: "sell", 4: "buy"}

    post_type_int = (
        await conn.fetchrow(
            f"SELECT making_post from profiles where user_id={event.author.id}"
        )
    ).get("making_post")

    if not post_type_int:
        await conn.close()
        return

    post_type = types.get(post_type_int)

    if post_type_int in [1, 2]:
        post = await conn.fetchrow(
            f"SELECT id, stage, guild_id, message_id, title from {post_type} where author_id='{event.author.id}' and pending_approval is FALSE and post_date is NULL"
        )
    else:
        post = await conn.fetchrow(
            f"SELECT id, stage, guild_id, message_id, author_id, title from {post_type} where author_id='{event.author.id}' and stage=4"
        )
    guild_id = post.get("guild_id")

    stage = post.get("stage")

    post_id = post.get("id")
    valid_stages = [2, 4]
    if not any(stage == num for num in valid_stages):
        await conn.close()
        return

    try:
        first_img = event.message.attachments[0]
        # print(
        #     f"Image for {post_type} post",
        #     first_img.media_type,
        #     first_img.filename,
        # )
        if "image" not in first_img.media_type:
            await event.author.send("Please send an image file that discord recognizes")
            await conn.close()
            return

        img_urls = ""
        for image in event.message.attachments[1:4]:
            if "image" in image.media_type:
                img_urls += f"{image.url}|"

        if stage == 2:
            msg_id = await conn.fetchval(f"SELECT image from sell where id={post_id}")
            await event.app.rest.edit_message(
                channel=event.channel_id, message=msg_id, components=[]
            )

        await conn.execute(
            f"UPDATE {post_type} set stage=3,image='{first_img.url}',add_images='{img_urls}' where id={post_id}"
        )
        embed = await buildPostEmbed(
            post_id=post_id, post_type=post_type, user=event.author
        )
        if stage == 2:
            if (len(event.message.attachments) >= 1) and (img_urls != ""):
                # remove components from msg9
                await event.author.send(
                    embed=embed,
                    components=await asyncio.gather(
                        flare.Row(
                            edit_select_menu(
                                post_id=post_id, post_type=post_type, guild_id=guild_id
                            )
                        ),
                        flare.Row(
                            ButtonSendPostToMods(
                                post_id=post_id, post_type=post_type, guild_id=guild_id
                            ),
                            ButtonNewPostPhotos(
                                post_id=post_id, post_type=post_type, guild_id=guild_id
                            ),
                            ButtonShowMoreImages(post_id=post_id, post_type=post_type),
                            ButtonCancel(
                                post_id=post_id, post_type=post_type, label="Cancel"
                            ),
                        ),
                    ),
                )
            else:
                await event.author.send(
                    embed=embed,
                    components=await asyncio.gather(
                        flare.Row(
                            edit_select_menu(
                                post_id=post_id, post_type=post_type, guild_id=guild_id
                            )
                        ),
                        flare.Row(
                            ButtonSendPostToMods(
                                post_id=post_id, post_type=post_type, guild_id=guild_id
                            ),
                            ButtonNewPostPhotos(
                                post_id=post_id, post_type=post_type, guild_id=guild_id
                            ),
                            ButtonCancel(
                                post_id=post_id, post_type=post_type, label="Cancel"
                            ),
                        ),
                    ),
                )

        if stage == 4:

            msg_id = post.get("message_id")
            await conn.execute(
                f"UPDATE profiles set making_post=0 where user_id = {event.author.id}"
            )
            await conn.execute(
                f"UPDATE sell set stage=3 where author_id='{event.author.id}' and stage=4"
            )
            guild = await conn.fetchrow(
                f"SELECT buy_channel_id, sell_channel_id from guilds where guild_id={guild_id}"
            )

            chnl_dict = {
                "sell": guild.get("sell_channel_id"),
                "buy": guild.get("buy_channel_id"),
            }
            print("img urls", img_urls)
            if img_urls != "":
                btns_row = await flare.Row(
                    ButtonContactLister(
                        post_id=post_id,
                        post_type=post_type,
                        post_owner_id=event.author.id,
                        post_title=post.get("title"),
                    ),
                    ButtonShowMoreImages(post_id=post_id, post_type=post_type),
                    ButtonReportPost(
                        post_id=post_id,
                        post_type=post_type,
                        post_owner_id=event.author.id,
                    ),
                    ButtonUpdatePost(
                        post_id=post_id,
                        post_type=post_type,
                        post_owner_id=event.author.id,
                    ),
                )
            else:
                btns_row = await flare.Row(
                    ButtonContactLister(
                        post_id=post_id,
                        post_type=post_type,
                        post_owner_id=event.author.id,
                        post_title=post.get("title"),
                    ),
                    ButtonShowMoreImages(post_id=post_id, post_type=post_type),
                    ButtonReportPost(
                        post_id=post_id,
                        post_type=post_type,
                        post_owner_id=event.author.id,
                    ),
                    ButtonUpdatePost(
                        post_id=post_id,
                        post_type=post_type,
                        post_owner_id=event.author.id,
                    ),
                )
            await posts_dms_plugin.bot.rest.edit_message(
                channel=chnl_dict.get(post_type),
                message=msg_id,
                embed=embed,
                component=btns_row,
            )

            await event.author.send("Images received and updated on your post")
            await send_public_log(
                guild_id=guild_id,
                text=f"**{post_type.upper()}:** <@{post.get('author_id')}> **UPDATED** listing __{post.get('title')}__ with new **IMAGE(S)**",
            )
        await conn.close()

    except:
        await event.author.send("No file attached")
        await conn.close()

    # add send buttons


def load(bot: lightbulb.BotApp):
    bot.add_plugin(posts_dms_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(posts_dms_plugin)
