import logging, os, sys, asyncpg, hikari
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

    print("Connecting To Database")
    dsn = os.getenv("DATABASE_CONN_STRING")

    pool = await asyncpg.create_pool(
        dsn=dsn,
        max_size=200,
        max_inactive_connection_lifetime=10,
    )
    print("pool connected and created")
    app.swapbotDBpool = pool


@app.after_serving
async def stopping():
    await app.discord_rest.close()


@app.route("/")
async def main():
    return redirect("/home")


@app.route("/login")
async def login():
    if 'token' not in session:
        return await render_template("login.html", oauth_uri=OAUTH_URI)
    
    if 'token' in session:
        return redirect("/home")


@app.route("/home")
async def home():
    if 'token' not in session:
        return redirect("/login")

    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()

        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)

        if row == None:
            return redirect("/noprofile")
        else:
            pfpImg = row.get('profile_picture')
            if pfpImg == None:
                pfpImg = 'static/assets/profile_placeholder.jpg'
            return await render_template("construction.html", current_user=my_user, avatar_url=pfpImg,
                                         user_id=my_user.id, current_name=my_user.username)


@app.route("/listings")
async def listings():
    if 'token' not in session:
        return redirect("/login")

    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        session['client_guilds'] = [f"{a.id}" for a in (await (client.fetch_my_guilds()))]
        my_user = await client.fetch_my_user()
        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1 and stage=4", my_user.id)
        if row == None:
            return redirect("/noprofile")
        else:
            guilds_str = ', '.join(f"'{i}'" for i in session['client_guilds'])
            pfpImg = row.get('profile_picture')
            data_sell = await app.swapbotDBpool.fetch(f"select sell.*,CONCAT(first_name, ' ', last_name) AS NAME, "
                                                      f"CAST((DATE_PART('day', CURRENT_DATE::date) - DATE_PART('day', sell.post_date::date)) AS INT) as DATE_DIFF "
                                                      f"from profiles JOIN sell on user_id = author_id "
                                                      f"where post_date IS NOT NULL and notified_expiry = FALSE and sell.guild_id IN ({guilds_str}) order by sell.id")
            data_buy = await app.swapbotDBpool.fetch(f"select buy.*,CONCAT(first_name, ' ', last_name) AS NAME, "
                                                     f"CAST((DATE_PART('day', CURRENT_DATE::date) - DATE_PART('day', buy.post_date::date)) AS INT) as DATE_DIFF "
                                                     f"from profiles JOIN buy on user_id = author_id "
                                                     f"where post_date IS NOT NULL and notified_expiry = FALSE and buy.guild_id IN ({guilds_str}) order by buy.id")

            if pfpImg == None:
                pfpImg = 'static/assets/profile_placeholder.jpg'
            return await render_template("listings.html", current_user=my_user,
                                         user_id=session['uid'], current_name=my_user.username,
                                         first_name=row.get('first_name'), last_name=row.get('last_name'),
                                         avatar_url=pfpImg, data_sell=data_sell, data_buy=data_buy)


@app.route("/about")
async def about():
    if 'token' not in session:
        return redirect("/")

    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()
        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
        if row == None:
            return redirect("/noprofile")
        else:
            pfpImg = row.get('profile_picture')
            if pfpImg == None:
                pfpImg = 'static/assets/profile_placeholder.jpg'
            return await render_template("about.html", current_user=my_user,
                                         user_id=my_user.id, current_name=my_user.username,
                                         first_name=row.get('first_name'), last_name=row.get('last_name'),
                                         avatar_url=pfpImg)


@app.route("/contact")
async def contact():
    if 'token' not in session:
        return redirect("/")

    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        client: hikari.impl.RESTClientImpl
        my_user = await client.fetch_my_user()

        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)

        if row == None:
            return redirect("/noprofile")
        else:
            fName = row.get('first_name')
            lName = row.get('last_name')
            pfpImg = row.get('profile_picture')
            if pfpImg == None:
                pfpImg = 'static/assets/profile_placeholder.jpg'
            return await render_template("contact.html", current_user=my_user,
                                         user_id=my_user.id, current_name=my_user.username,
                                         first_name=fName, last_name=lName,
                                         avatar_url=pfpImg, EuName=session['EuName'], ZuName=session['ZuName'],
                                         Epfp=session['Epfp'], Zpfp=session['Zpfp'])


@app.route("/profile")
async def profile():
    if 'token' not in session:
        return redirect("/make-profile")

    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()
        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
        if row == None:
            return redirect("/make-profile")
        else:
            pfpImg = row.get('profile_picture')
            if pfpImg == None:
                pfpImg = 'static/assets/profile_placeholder.jpg'
            return await render_template("profile.html", current_user=my_user, avatar_url=pfpImg,
                                         user_id=my_user.id, current_name=my_user.username,
                                         first_name=row.get('first_name'), last_name=row.get('last_name'),
                                         pronouns=row.get('pronouns'), email=row.get('email'), pfp=pfpImg)


@app.route("/make-profile")
async def makeProf():
    if 'token' not in session:
        return redirect("/")

    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        if session['pfpURL'] == None:
            pfpImg = 'static/assets/profile_placeholder.jpg'
        else:
            pfpImg = session['pfpURL']

        my_user = await client.fetch_my_user()
        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1 and stage=4", my_user.id)
        if row == None:
            print('PAGE LOAD: ' + pfpImg)
            return await render_template("make-profile.html", current_user=my_user, avatar_url=pfpImg,
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

    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()
        async with app.discord_rest.acquire(BOT_TOKEN, hikari.TokenType.BOT) as bot_client:
            row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
            first_name = row.get("first_name")
            last_name = row.get("last_name")
            await bot_client.create_message(CHANNEL_ID,
                                            content=f"Message Successfully Sent from Website\n{first_name} {last_name}")
    return redirect("/")


@app.route("/submitInfo", methods=["POST", "GET"])
async def submitInfo():
    if request.method == "GET":
        return "The URL /submitInfo is accessed directly. Try going to '/form' to submit form"
    if request.method == "POST":

        prof = await request.form
        fName = prof.get("fname")
        lName = prof.get("lname")
        pNouns = prof.get("pnouns")
        email = prof.get("email")

        # print(fName + ' | ' + pNouns + ' | ' + pNouns + ' | ' + email)
        # print("Submit Successful")
        # print('PFP SUBMIT: ' + session['pfpURL'])
        async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
            my_user = await client.fetch_my_user()
            row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
            if row == None:
                await app.swapbotDBpool.execute(
                    "INSERT INTO profiles (first_name, last_name, pronouns, email, user_id, profile_picture, stage) VALUES ($1, $2, $3, $4, $5, $6, 4)",
                    fName, lName, pNouns, email, session['uid'], session['pfpURL'])
            else:
                await app.swapbotDBpool.execute(
                    "UPDATE profiles set first_name=$1, last_name=$2, pronouns=$3, email=$4, profile_picture=$6, stage=4 where user_id=$5",
                    fName, lName, pNouns, email, session['uid'], session['pfpURL'])
        return redirect("/profile")


@app.route("/submitPFP", methods=["POST"])
async def submitPFP():
    if request.method == "POST":
        pfpIMG = (await request.files)['pfpFile'].read()

        print(f"PFP Submit Successful by UID: {session['uid']}")

        async with app.discord_rest.acquire(BOT_TOKEN, hikari.TokenType.BOT) as bot_client:
            bot_client: hikari.impl.RESTClientImpl
            dmChan = await bot_client.create_dm_channel(session['uid'])
            pfpProxy = hikari.Embed(title="UPLOAD SUCCESSFUL:  New PFP Uploaded")
            pfpProxy.set_image(pfpIMG)
            dmEmbed = await dmChan.send(embed=pfpProxy)
            session['pfpURL'] = dmEmbed.embeds[0].image.url

            # async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
            #     my_user = await client.fetch_my_user()
            #     row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
            #     if row == None:
            #         await app.swapbotDBpool.execute("INSERT INTO profiles (profile_picture, user_id) VALUES ($1, $2)", pfpURL, session['uid'])
            #     else:
            #         await app.swapbotDBpool.execute("UPDATE profiles set profile_picture=$1 where user_id=$2", pfpURL, session['uid'])

        return redirect("/profile")


@app.route("/construction")
async def construction():
    if 'token' not in session:
        return redirect("/")

    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        my_user = await client.fetch_my_user()

        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)

        if row == None:
            return redirect("/noprofile")
        else:
            pfpImg = row.get('profile_picture')
            if pfpImg == None:
                pfpImg = 'static/assets/profile_placeholder.jpg'
            return await render_template("construction.html", current_user=my_user, avatar_url=pfpImg,
                                         user_id=my_user.id, current_name=my_user.username)


async def background_task():
    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        session['client_guilds'] = [a.id for a in (await (client.fetch_my_guilds()))]


@app.route("/auth/discord")
async def callback():
    session.clear()
    session.permanent = False

    code = request.args.get('code')
    # async with app.discord_rest.acquire(None) as r:
    #     token = (await r.authorize_access_token(
    #         int(CLIENT_ID), CLIENT_SECRET, code, REDIRECT_URI
    #     ))
    #
    #     access_token = token.access_token
    # await app.token.acquire(app.discord_rest) = access_token

    # async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
    #     my_user = await client.fetch_my_user()
    #     row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
    #     # async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
    #     session['client_guilds'] = [f"{a.id}" for a in (await (client.fetch_my_guilds()))]
    #     session['uid'] = my_user.id
    #
    #     if row == None:
    #         session['pfpURL'] = None
    #     else:
    #         session['pfpURL'] = row.get('profile_picture')
    #     print('AUTHORIZATION')

    from Website.new import UserCredentialsStrategy
    # from hikari.impl.rest import UserCredentialsStrategy
    session["token"] = True
    app.token = UserCredentialsStrategy(client_id=CLIENT_ID, client_secret=CLIENT_SECRET, redirect_uri=REDIRECT_URI, code=code)

    async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest)) as client:
        my_user = await client.fetch_my_user()
        row = await app.swapbotDBpool.fetchrow(f"Select * from profiles where user_id = $1", my_user.id)
        # async with app.discord_rest.acquire(await app.token.acquire(app.discord_rest), hikari.TokenType.BEARER) as client:
        session['client_guilds'] = [f"{a.id}" for a in (await (client.fetch_my_guilds()))]
        session['uid'] = my_user.id

        if row == None:
            session['pfpURL'] = None
        else:
            session['pfpURL'] = row.get('profile_picture')
        print('AUTHORIZATION')

    async with app.discord_rest.acquire(BOT_TOKEN, hikari.TokenType.BOT) as bot_client:
        bot_client: hikari.impl.RESTClientImpl
        elijah = await bot_client.fetch_user(138128209517477888)
        zach = await bot_client.fetch_user(304796852476444673)
        session['Epfp'] = str(elijah.avatar_url)
        session['Zpfp'] = str(zach.avatar_url)
        session['EuName'] = elijah.username
        session['ZuName'] = zach.username

    # app.add_background_task(background_task)

    return redirect("/home")


async def create_channels(post_type: str, post_id: int):
    from Website.contact_from_web import contact_channel_from_web
    await contact_channel_from_web(post_id=post_id, post_type=post_type, int_party_id=session['uid'],
                                   restApp=app.discord_rest, conn=await app.swapbotDBpool.acquire())


@app.route("/contact-lister/<posttype>/<postid>/<intid>")
async def contact_lister(posttype, postid, intid):
    app.add_background_task(create_channels, posttype, postid)
    # await create_channels(post_type=posttype, post_id=postid)
    return redirect("/home")


async def send_profile(author_id, user_id, guild_id):
    from Website.contact_from_web import send_user_profile
    await send_user_profile(author_id, user_id, guild_id, app.discord_rest, await app.swapbotDBpool.acquire())


@app.route("/view-profile/<author_id>/<user_id>/<guild_id>")
async def view_profile(author_id, user_id, guild_id):
    app.add_background_task(send_profile, author_id, user_id, guild_id)
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
