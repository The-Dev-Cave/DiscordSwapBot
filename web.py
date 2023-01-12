import logging
import os
from dotenv import load_dotenv

import hikari
import flare
from quart import Quart, session, render_template, redirect, request

load_dotenv()

logging.basicConfig(level="WARN")
app = Quart(__name__, template_folder='Website/pages')
app.secret_key = os.urandom(12)
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIRECT_URI = os.getenv("REDIRECT_URI")
OAUTH_URI = os.getenv("OAUTH_URI")
CLIENT_ID = int(os.getenv("CLIENT_ID"))
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CHANNEL_ID = int(os.environ["CHANNEL_ID"])  # Channel to post in as an int


@app.before_serving
async def starting():
    app.discord_rest = hikari.RESTApp()
    await app.discord_rest.start()


@app.after_serving
async def stopping():
    await app.discord_rest.close()


@app.route("/logout")
async def logout():
    session.clear()
    return redirect("/")


@app.route("/", methods=["POST"])
async def testPost():
    async with app.discord_rest.acquire(BOT_TOKEN, hikari.TokenType.BOT) as bot_client:
        await bot_client.create_message(CHANNEL_ID, content="Message Successfully Sent from Website")
    return redirect("/")

@app.route("/")
async def home():
    if 'token' not in session:
        return await render_template("index.html", oauth_uri=OAUTH_URI)

    async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()
        return await render_template("index.html", current_user=my_user, avatar_url=my_user.avatar_url,
                                     user_id=my_user.id)


async def background_task():
    async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
        session['client_guilds'] = [a.id for a in (await (client.fetch_my_guilds()))]


@app.route("/auth/discord")
async def callback():
    session.clear()
    session.permanent = False

    code = request.args.get('code')
    async with app.discord_rest.acquire(None) as r:
        token = (await r.authorize_access_token(
            int(CLIENT_ID), CLIENT_SECRET, code, REDIRECT_URI
        ))

        access_token = token.access_token
    session['token'] = access_token

    app.add_background_task(background_task)

    # async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
    #     session['client_guilds'] = [a.id for a in (await (client.fetch_my_guilds()))]
    # my_user = await client.fetch_my_user()
    # async with app.discord_rest.acquire(BOT_TOKEN, hikari.TokenType.BOT) as bot_client:
    #     from bot.interactions.buttons.buttons_posts import ButtonCreatePost
    #     # session['bot_guilds'] = [a.id for a in (await (bot_client.fetch_my_guilds()))]
    #     bot_client: hikari.impl.RESTClientImpl
    #     buttons = await flare.Row(
    #         ButtonCreatePost(post_type="selling", label="I'm Looking To Sell"),
    #         ButtonCreatePost(post_type="buying", label="I'm Looking To Buy"),
    #         ButtonCreatePost(post_type="trading", label="I'm Looking To Trade"),
    #     )
    #     await bot_client.create_message(1059970851400863826, content="test", component=buttons)
    return redirect("/")


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=443, keyfile="./Website/certs/rootCAKey.pem", certfile="./Website/certs/rootCACert.pem")
    #app.run(port=8080)
