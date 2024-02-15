


import sys
import asyncio

from bot import start_bot

from handlers.bot_callback import bot
from handlers.bot_newmessage import bot

from proxies import update_available_proxies

async def main():
    await start_bot()
    while True:
        print("start proxie checker")
        loop.run_in_executor(None, update_available_proxies)
        await asyncio.sleep(10*60)

loop = asyncio.get_event_loop()
try:
    asyncio.ensure_future(main())
    loop.run_forever()
except KeyboardInterrupt:
    print('trying to disconnect...')
except Exception as e:
    print('got error: ', e)
finally:
    print("bot has been disconnected")
    sys.exit()
