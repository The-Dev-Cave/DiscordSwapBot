import asyncpg
import lightbulb
import os
import hikari
from lightbulb.ext import tasks

database_plugin = lightbulb.Plugin("Database Functions", include_datastore=True)


async def create_pool() -> None:
    print("Connecting To Database")
    dsn = f'{os.getenv("DATABASE_CONN_STRING")}'
    pool = await asyncpg.create_pool(
        dsn=dsn,
        max_size=200,
        max_inactive_connection_lifetime=10,
    )
    database_plugin.bot.d.pool = pool
    print("pool connected and created")


async def get_database_connection() -> asyncpg.Connection:
    pool: asyncpg.Pool = database_plugin.bot.d.get("pool")
    return await pool.acquire()


# @tasks.task(s=1, auto_start=True, wait_before_execution=True)
# # @tasks.task(tasks.CronTrigger("59 6 * * *"), auto_start=True)
# async def expired():
#     try:
#         print(database_plugin.d.pool.get_idle_size())
#     except:
#         pass


def load(bot: lightbulb.BotApp):
    bot.add_plugin(database_plugin)


def unload(bot: lightbulb.BotApp):
    bot.remove_plugin(database_plugin)
