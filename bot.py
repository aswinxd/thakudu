import sys
import glob
import importlib
from pathlib import Path
from pyrogram import idle
import logging
import logging.config
import asyncio
from datetime import date, datetime
import pytz
from aiohttp import web

from config import LOG_CHANNEL, ON_HEROKU, CLONE_MODE, PORT
from Script import script
from plugins.clone import restart_bots
from TechVJ.server import web_server
from TechVJ.bot import StreamBot
from TechVJ.utils.keepalive import ping_server
from TechVJ.bot.clients import initialize_clients



logging.config.fileConfig('logging.conf')
logging.getLogger().setLevel(logging.INFO)
logging.getLogger("pyrogram").setLevel(logging.ERROR)


ppath = "plugins/*.py"
files = glob.glob(ppath)


async def start():
    print('\nInitializing Tech VJ Bot')

    try:
        await StreamBot.start()
        me = await StreamBot.get_me()
        logging.info(f"Connected as {me.first_name} (@{me.username})")
    except Exception as e:
        logging.error(f"Failed to start StreamBot: {e}")
        return

    await initialize_clients()

    for name in files:
        with open(name) as a:
            patt = Path(a.name)
            plugin_name = patt.stem.replace(".py", "")
            plugins_dir = Path(f"plugins/{plugin_name}.py")
            import_path = f"plugins.{plugin_name}"
            spec = importlib.util.spec_from_file_location(import_path, plugins_dir)
            load = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(load)
            sys.modules["plugins." + plugin_name] = load
            print(f"Imported => {plugin_name}")

    if ON_HEROKU:
        asyncio.create_task(ping_server())

    tz = pytz.timezone('Asia/Kolkata')
    today = date.today()
    now = datetime.now(tz)
    time = now.strftime("%H:%M:%S %p")

    app = web.AppRunner(await web_server())
    await StreamBot.send_message(chat_id=LOG_CHANNEL, text=script.RESTART_TXT.format(today, time))
    await app.setup()
    bind_address = "0.0.0.0"
    await web.TCPSite(app, bind_address, PORT).start()

    if CLONE_MODE:
        await restart_bots()

    print("Bot Started powered by andi")
    await idle()


if __name__ == '__main__':
    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(start())
    except KeyboardInterrupt:
        logging.info('Service Stopped Bye 👋')
    except Exception as e:
        logging.error(f"Unhandled exception: {e}")




