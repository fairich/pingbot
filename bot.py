from telethon.sync import TelegramClient
from telethon import events
from telethon.tl.types import ChannelParticipantsAdmins
import asyncio
import os
import requests
from threading import Thread
import time
from flask import Flask
import json

app = Flask(__name__)

# Конфигурация
api_id = int(os.environ.get('API_ID'))
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')
RENDER_URL = "https://ping-bot-asa4.onrender.com"

# Создаем event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Создаем клиент Telegram
client = TelegramClient('bot_session', api_id, api_hash, loop=loop)

class DataStore:
    def __init__(self):
        self.ping_list = set()
        self.last_ping_time = {}
        self.load_data()
    
    def load_data(self):
        try:
            with open('bot_data.json', 'r') as f:
                data = json.load(f)
                self.ping_list = set(data.get('ping_list', []))
                self.last_ping_time = data.get('last_ping_time', {})
        except FileNotFoundError:
            pass

    def save_data(self):
        data = {
            'ping_list': list(self.ping_list),
            'last_ping_time': self.last_ping_time
        }
        with open('bot_data.json', 'w') as f:
            json.dump(data, f)

data_store = DataStore()

def split_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

async def check_cooldown(command_type, chat_id):
    current_time = time.time()
    last_time = data_store.last_ping_time.get(f"{command_type}_{chat_id}", 0)
    if current_time - last_time < 1800:  # 30 минут
        remaining = 1800 - (current_time - last_time)
        return False, int(remaining)
    data_store.last_ping_time[f"{command_type}_{chat_id}"] = current_time
    return True, 0

@client.on(events.NewMessage(pattern=r'^/all$'))
async def all_cmd(event):
    try:
        chat = await event.get_chat()
        
        # Проверяем кулдаун
        can_ping, remaining = await check_cooldown('all', chat.id)
        if not can_ping:
            await event.respond(f"⏳ Подождите еще {remaining//60} минут и {remaining%60} секунд")
            return

        # Получаем всех участников
        participants = await client.get_participants(chat)
        mentions = []

        # Формируем список упоминаний
        for user in participants:
            if not user.bot and not user.deleted:
                mentions.append(f"[{user.first_name}](tg://user?id={user.id})")

        if not mentions:
            await event.respond("❌ Не удалось получить список пользователей")
            return

        # Разбиваем на группы и отправляем
        mention_groups = split_list(mentions, 20)
        for group in mention_groups:
            await event.respond("📢 Внимание!\n" + " ".join(group))
            await asyncio.sleep(2)

    except Exception as e:
        print(f"Ошибка в all_cmd: {str(e)}")
        await event.respond("Произошла ошибка при выполнении команды")

@client.on(events.NewMessage(pattern=r'^/ping$'))
async def ping_cmd(event):
    try:
        chat = await event.get_chat()
        
        # Проверяем кулдаун
        can_ping, remaining = await check_cooldown('ping', chat.id)
        if not can_ping:
            await event.respond(f"⏳ Подождите еще {remaining//60} минут и {remaining%60} секунд")
            return

        # Получаем всех участников
        participants = await client.get_participants(chat)
        mentions = []

        # При первом запуске добавляем всех в список пинга
        if not data_store.ping_list:
            for user in participants:
                if not user.bot and not user.deleted:
                    data_store.ping_list.add(user.id)
            data_store.save_data()

        # Формируем список упоминаний ТОЛЬКО из тех, кто в списке ping_list
        for user in participants:
            if not user.bot and not user.deleted:
                # Проверяем, есть ли пользователь в списке ping_list
                if user.id in data_store.ping_list:
                    mentions.append(f"[{user.first_name}](tg://user?id={user.id})")

        if not mentions:
            await event.respond("❌ Нет пользователей для уведомления")
            return

        # Разбиваем на группы и отправляем
        mention_groups = split_list(mentions, 20)
        for group in mention_groups:
            await event.respond("🔔 Пинг!\n" + " ".join(group))
            await asyncio.sleep(2)

    except Exception as e:
        print(f"Ошибка в ping_cmd: {str(e)}")
        await event.respond("Произошла ошибка при выполнении команды")

@client.on(events.NewMessage(pattern=r'^/pingoff$'))
async def pingoff_cmd(event):
    try:
        user_id = event.sender_id
        # Удаляем пользователя из списка ping_list
        if user_id in data_store.ping_list:
            data_store.ping_list.remove(user_id)
            data_store.save_data()
            await event.respond("✅ Вы отключили уведомления")
        else:
            await event.respond("❌ Вы уже отключили уведомления")
    except Exception as e:
        print(f"Ошибка в pingoff_cmd: {str(e)}")
        await event.respond("Произошла ошибка при выполнении команды")

@client.on(events.NewMessage(pattern=r'^/pingon$'))
async def pingon_cmd(event):
    try:
        user_id = event.sender_id
        # Добавляем пользователя в список ping_list
        if user_id not in data_store.ping_list:
            data_store.ping_list.add(user_id)
            data_store.save_data()
            await event.respond("✅ Вы включили уведомления")
        else:
            await event.respond("❌ Уведомления уже включены")
    except Exception as e:
        print(f"Ошибка в pingon_cmd: {str(e)}")
        await event.respond("Произошла ошибка при выполнении команды")

@app.route('/')
def home():
    return "Bot is running!"

def keep_alive():
    while True:
        try:
            requests.get(RENDER_URL)
            print("Пинг отправлен - бот активен")
        except Exception as e:
            print(f"Ошибка пинга: {str(e)}")
        time.sleep(780)

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def main():
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    keep_alive_thread = Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    
    with client:
        client.start(bot_token=bot_token)
        print("Бот успешно запущен!")
        client.run_until_disconnected()

if __name__ == '__main__':
    main()