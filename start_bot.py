import asyncio
import os

import hikari

from BotCode.create_bot import create_bot

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop

        uvloop.install()
    asyncio.run(create_bot()).run(
        status=hikari.Status.ONLINE, activity=hikari.Activity(
            name="Marketing",
            type=hikari.ActivityType.COMPETING,
        ))
