from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins
import asyncio
import os
import requests
from threading import Thread
import time

# Получаем данные из переменных окружения
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')

# URL вашего приложения на Render
RENDER_URL = "https://ping-bot-asa4.onrender.com"

# Функция для поддержания бота активным
def keep_alive():
    while True:
        try:
            requests.get(RENDER_URL)
            print("Пинг отправлен")
        except:
            print("Ошибка пинга")
        time.sleep(60)  # Пинг каждые 13 минут

# Создаем и запускаем поток для пинга
keep_alive_thread = Thread(target=keep_alive)
keep_alive_thread.daemon = True  # Поток будет завершен вместе с основной программой
keep_alive_thread.start()

# Создаем клиент
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage(pattern='/all'))
async def all_cmd(event):
    chat = await event.get_chat()
    
    # Получаем всех участников чата
    participants = await client.get_participants(chat)
    
    # Формируем сообщение с тегами
    mentions = []
    for user in participants:
        if not user.bot:  # Пропускаем ботов
            mentions.append(f"[{user.first_name}](tg://user?id={user.id})")
    
    # Отправляем сообщение с тегами
    await event.respond("Внимание!\n" + " ".join(mentions))

# Запускаем бота
client.run_until_disconnected()