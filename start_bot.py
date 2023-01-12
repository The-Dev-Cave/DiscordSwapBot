import asyncio
import os

from BotCode.create_bot import create_bot

if __name__ == "__main__":
    if os.name != "nt":
        import uvloop
        print("UVLOOP")
        uvloop.install()
    asyncio.run(create_bot()).run()
