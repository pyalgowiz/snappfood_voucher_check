from telethon.sync import TelegramClient, connection

api_id = 1
api_hash = 'hash'

snappcheck_bot = 'bot token'

bot = TelegramClient(f"sessions/{str(snappcheck_bot)}", api_id, api_hash)
bot.parse_mode = 'html'

async def start_bot() -> TelegramClient:
    await bot.start(bot_token=snappcheck_bot)
    print('panel bot: snappcheck_bot')
    return bot
