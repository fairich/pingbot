from telethon.sync import TelegramClient  # изменен импорт
from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins
import asyncio
import os
import requests
from threading import Thread
import time
from flask import Flask

app = Flask(__name__)

# Получаем данные из переменных окружения
api_id = int(os.environ.get('API_ID'))
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')

# URL вашего приложения на Render
RENDER_URL = "https://ping-bot-asa4.onrender.com"

# Создаем event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Создаем клиент Telegram
client = TelegramClient('bot_session', api_id, api_hash, loop=loop)

@app.route('/')
def home():
    return "Bot is running!"

@client.on(events.NewMessage(pattern='/all'))
async def all_cmd(event):
    chat = await event.get_chat()
    participants = await client.get_participants(chat)
    mentions = []
    for user in participants:
        if not user.bot:
            mentions.append(f"[{user.first_name}](tg://user?id={user.id})")
    await event.respond("Внимание!\n" + " ".join(mentions))

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def main():
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаем бота
    with client:
        client.start(bot_token=bot_token)
        print("Bot started successfully!")
        client.run_until_disconnected()

if __name__ == '__main__':
    main()