import logging, os, sys, ssl, asyncpg, hikari, json
from io import BytesIO
from dotenv import load_dotenv

from quart import Quart, session, render_template, redirect, request

load_dotenv()

logging.basicConfig(level="WARN")
app = Quart(__name__, template_folder='Website/templates', static_folder='Website/static')
app.secret_key = os.urandom(12)
BOT_TOKEN = os.getenv("BOT_TOKEN")
REDIRECT_URI = os.getenv("REDIRECT_URI")
OAUTH_URI = os.getenv("OAUTH_URI")
CLIENT_ID = int(os.getenv("CLIENT_ID"))
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
CHANNEL_ID = int(os.environ["CHANNEL_ID"])  # Channel to post in as an int
MODE = os.getenv("MODE")

UPLOAD_FOLDER = '/root/DiscordSwapBot/Website/certs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Reveal type for type hinting when coding
app.swapbotDBpool: asyncpg.Pool
app.discord_rest: hikari.RESTApp

@app.before_serving
async def starting():
    app.discord_rest = hikari.RESTApp()
    await app.discord_rest.start()

    sslctx = ssl.create_default_context(ssl.Purpose.SERVER_AUTH,
                                        cafile=r"Website/certs/SwapBot-PostgreSQL-ca-certificate.crt")
    sslctx.check_hostname = True
    print("Connecting To Database")
    dsn = os.getenv("DATABASE_CONN_STRING")

    pool = await asyncpg.create_pool(
        dsn=dsn,
        max_size=200,
        max_inactive_connection_lifetime=10,
        ssl=sslctx,
    )
    print("pool connected and created")
    app.swapbotDBpool = pool

@app.after_serving
async def stopping():
    await app.discord_rest.close()


@app.route("/")
async def login():
    if 'token' not in session:
        return await render_template("login.html", oauth_uri=OAUTH_URI)

    if 'token' in session:
        return redirect("/home")


@app.route("/home")
async def home():
    if 'token' not in session:
        return redirect("/")

    async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()
        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
        if row == None:
            return redirect("/noprofile")
        else:
            return await render_template("home.html", current_user=my_user, avatar_url=my_user.avatar_url,
                                        user_id=my_user.id, current_name=my_user.username, first_name=row.get('first_name'), last_name=row.get('last_name'))


@app.route("/profile")
async def profile():
    if 'token' not in session:
        return redirect("/")

    async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()
        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
        if row == None:
            return redirect("/noprofile")
        else:
            if row.get('profile_picture') == None:
                avatar = 'static/assets/profile_placeholder.jpg'
            else:
                avatar = row.get('profile_picture')
            return await render_template("profile.html", current_user=my_user, avatar_url=my_user.avatar_url,
                                        user_id=my_user.id, current_name=my_user.username, 
                                        first_name=row.get('first_name'), last_name=row.get('last_name'),
                                        pronouns=row.get('pronouns'), email=row.get('email'), pfp=avatar)


@app.route("/make-profile")
async def makeProf():
    if 'token' not in session:
        return redirect("/")
    
    async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()
        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
        if row == None:
            return await render_template("make-profile.html", current_user=my_user, avatar_url=my_user.avatar_url,
                                        user_id=my_user.id, current_name=my_user.username)
        else:
            return redirect("/home")


@app.route("/noprofile")
async def noprof():
    if 'token' not in session:
        return redirect("/")
    else:
        return await render_template("no-profile.html")


@app.route("/logout")
async def logout():
    session.clear()
    return redirect("/")


@app.route("/testPost")
async def testPost():
    if 'token' not in session:
        return

    async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()
        async with app.discord_rest.acquire(BOT_TOKEN, hikari.TokenType.BOT) as bot_client:
            row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
            first_name = row.get("first_name")
            last_name = row.get("last_name")
            await bot_client.create_message(CHANNEL_ID, content=f"Message Successfully Sent from Website\n{first_name} {last_name}")
    return redirect("/")


@app.route("/submitInfo", methods=["POST", "GET"])
async def submitInfo():
    if request.method == "GET":
        return "The URL /submitInfo is accessed directly. Try going to '/form' to submit form"
    if request.method == "POST":

        prof = await request.form
        print(prof)
        fName = prof.get("fname")
        lName = prof.get("lname")
        pNouns = prof.get("pnouns")
        email = prof.get("email")
        print(fName + ' | ' + pNouns + ' | ' + email)
        print("Submit Successful")

        async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
            my_user = await client.fetch_my_user()
            row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
            if row == None:
                await app.swapbotDBpool.execute("INSERT INTO profiles (first_name, last_name, pronouns, email, user_id) VALUES ($1, $2, $3, $4, $5)", fName, lName, pNouns, email, session['uid'])
            else:
                await app.swapbotDBpool.execute("UPDATE profiles set first_name=$1, last_name=$2, pronouns=$3, email=$4 where user_id=$5", fName, lName, pNouns, email, session['uid'])
        return redirect("/profile")


@app.route("/submitPFP", methods=["POST"])
async def submitPFP():
    if request.method == "POST":
        image = (await request.files)['file']
        buffer = BytesIO()
        img = await image.save(buffer)
        print(img)
        print("Submit Successful")

        # async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
        #     my_user = await client.fetch_my_user()
        #     row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
        #     if row == None:
        #         await app.swapbotDBpool.execute("INSERT INTO profiles (first_name, last_name, pronouns, email, user_id) VALUES ($1, $2, $3, $4, $5)", fName, lName, pNouns, email, session['uid'])
        #     else:
        #         await app.swapbotDBpool.execute("UPDATE profiles set first_name=$1, last_name=$2, pronouns=$3, email=$4 where user_id=$5", fName, lName, pNouns, email, session['uid'])
        return redirect("/profile")


@app.route("/construction")
async def construction():
    if 'token' not in session:
        return redirect("/")

    async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()
        return await render_template("construction.html", current_user=my_user, avatar_url=my_user.avatar_url,
                                     user_id=my_user.id, current_name=my_user.username)


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

    async with app.discord_rest.acquire(session['token'], hikari.TokenType.BEARER) as client:
        user = await client.fetch_my_user()
        session['uid'] = user.id

    app.add_background_task(background_task)
    return redirect("/home")


if __name__ == "__main__":
    if sys.argv[0] == 'dev' or MODE == 'dev':
        print("Starting in dev mode.")
        app.run(host='0.0.0.0',
                port=8080,
                debug=True,
                use_reloader=True
                )
    else:
        print("Starting in prod mode.")
        app.run(host='0.0.0.0',
                port=443,
                keyfile="./Website/certs/rootCAKey.pem",
                certfile="./Website/certs/rootCACert.pem",
                )
