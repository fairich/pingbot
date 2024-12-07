from telethon import TelegramClient, events
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

# Создаем клиент Telegram
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

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

def run_bot():
    client.run_until_disconnected()

if __name__ == '__main__':
    # Запускаем бота в отдельном потоке
    bot_thread = Thread(target=run_bot)
    bot_thread.start()
    
    # Запускаем веб-сервер
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)