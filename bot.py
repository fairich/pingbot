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
from datetime import datetime, timedelta

app = Flask(__name__)

# Конфигурация
api_id = int(os.environ.get('API_ID'))
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')
RENDER_URL = "https://ping-bot-asa4.onrender.com"

# Создаем event loop
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

# Создаем клиент Telegram - ВАЖНО: объявляем ДО декораторов
client = TelegramClient('bot_session', api_id, api_hash, loop=loop)

# Хранение данных
class DataStore:
    def __init__(self):
        self.main_list = set()
        self.ping_list = set()
        self.message_stats = {}
        self.last_ping_time = {}
        self.load_data()

    def load_data(self):
        try:
            with open('bot_data.json', 'r') as f:
                data = json.load(f)
                self.main_list = set(data.get('main_list', []))
                self.ping_list = set(data.get('ping_list', []))
                self.message_stats = data.get('message_stats', {})
                self.last_ping_time = data.get('last_ping_time', {})
        except FileNotFoundError:
            pass

    def save_data(self):
        data = {
            'main_list': list(self.main_list),
            'ping_list': list(self.ping_list),
            'message_stats': self.message_stats,
            'last_ping_time': self.last_ping_time
        }
        with open('bot_data.json', 'w') as f:
            json.dump(data, f)

data_store = DataStore()

# Функция для проверки кулдауна
async def check_cooldown(command_type, chat_id):
    current_time = time.time()
    last_time = data_store.last_ping_time.get(f"{command_type}_{chat_id}", 0)
    if current_time - last_time < 3600:  # 1 час
        remaining = 3600 - (current_time - last_time)
        return False, int(remaining)
    data_store.last_ping_time[f"{command_type}_{chat_id}"] = current_time
    return True, 0

# Разделение списка на группы
def split_list(lst, n):
    return [lst[i:i + n] for i in range(0, len(lst), n)]

# Обработчики команд
@client.on(events.NewMessage(pattern='/all'))
async def all_cmd(event):
    try:
        chat = await event.get_chat()
        can_ping, remaining = await check_cooldown('all', chat.id)
        if not can_ping:
            await event.respond(f"⏳ Подождите еще {remaining//60} минут и {remaining%60} секунд")
            return

        participants = await client.get_participants(chat)
        mentions = []
        for user in participants:
            if not user.bot:
                data_store.main_list.add(user.id)
                mentions.append(f"[{user.first_name}](tg://user?id={user.id})")

        mention_groups = split_list(mentions, 20)
        for group in mention_groups:
            await event.respond("📢 Внимание!\n" + " ".join(group))
            await asyncio.sleep(2)
        
        data_store.save_data()

    except Exception as e:
        print(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern='/ping'))
async def ping_cmd(event):
    try:
        chat = await event.get_chat()
        can_ping, remaining = await check_cooldown('ping', chat.id)
        if not can_ping:
            await event.respond(f"⏳ Подождите еще {remaining//60} минут и {remaining%60} секунд")
            return

        mentions = []
        for user_id in data_store.ping_list:
            try:
                user = await client.get_entity(user_id)
                mentions.append(f"[{user.first_name}](tg://user?id={user.id})")
            except:
                continue

        if not mentions:
            await event.respond("📝 Список пользователей пуст")
            return

        mention_groups = split_list(mentions, 20)
        for group in mention_groups:
            await event.respond("🔔 Пинг!\n" + " ".join(group))
            await asyncio.sleep(2)

    except Exception as e:
        print(f"Ошибка: {str(e)}")

@client.on(events.NewMessage(pattern='/pingoff'))
async def pingoff_cmd(event):
    user_id = event.sender_id
    if user_id in data_store.ping_list:
        data_store.ping_list.remove(user_id)
        data_store.save_data()
        await event.respond("✅ Вы отключили уведомления")
    else:
        await event.respond("❌ Вы уже отключили уведомления")

@client.on(events.NewMessage(pattern='/pingon'))
async def pingon_cmd(event):
    user_id = event.sender_id
    if user_id not in data_store.ping_list:
        data_store.ping_list.add(user_id)
        data_store.save_data()
        await event.respond("✅ Вы включили уведомления")
    else:
        await event.respond("❌ Уведомления уже включены")

@client.on(events.NewMessage(pattern='/top'))
async def top_cmd(event):
    try:
        chat = await event.get_chat()
        chat_id = str(chat.id)
        
        current_time = datetime.now()
        week_ago = current_time - timedelta(days=7)
        
        # Фильтруем и сортируем статистику
        chat_stats = data_store.message_stats.get(chat_id, {})
        weekly_stats = {
            user_id: count for user_id, (count, last_msg_time) in chat_stats.items()
            if datetime.fromtimestamp(last_msg_time) > week_ago
        }
        
        sorted_users = sorted(weekly_stats.items(), key=lambda x: x[1], reverse=True)[:20]
        
        if not sorted_users:
            await event.respond("📊 Нет статистики за последнюю неделю")
            return

        result = "📊 Топ 20 активных участников за неделю:\n\n"
        for i, (user_id, count) in enumerate(sorted_users, 1):
            try:
                user = await client.get_entity(int(user_id))
                result += f"{i}. {user.first_name} - {count} сообщений\n"
            except:
                continue

        await event.respond(result)

    except Exception as e:
        print(f"Ошибка: {str(e)}")

# Отслеживание сообщений для статистики
@client.on(events.NewMessage)
async def count_messages(event):
    if event.is_private:
        return

    try:
        chat_id = str(event.chat_id)
        user_id = str(event.sender_id)
        current_time = time.time()

        if chat_id not in data_store.message_stats:
            data_store.message_stats[chat_id] = {}

        if user_id not in data_store.message_stats[chat_id]:
            data_store.message_stats[chat_id][user_id] = [0, current_time]

        count, _ = data_store.message_stats[chat_id][user_id]
        data_store.message_stats[chat_id][user_id] = [count + 1, current_time]

        # Сохраняем данные каждые 100 сообщений
        if sum(stats[0] for stats in data_store.message_stats[chat_id].values()) % 100 == 0:
            data_store.save_data()

    except Exception as e:
        print(f"Ошибка при подсчете сообщений: {str(e)}")

def keep_alive():
    while True:
        try:
            requests.get(RENDER_URL)
            print("Пинг отправлен - бот активен")
        except Exception as e:
            print(f"Ошибка пинга: {str(e)}")
        time.sleep(780)  # Пинг каждые 13 минут

# Очистка старой статистики
async def cleanup_old_stats():
    while True:
        try:
            current_time = datetime.now()
            week_ago = current_time - timedelta(days=7)
            
            for chat_id in data_store.message_stats:
                data_store.message_stats[chat_id] = {
                    user_id: [count, last_time]
                    for user_id, (count, last_time) in data_store.message_stats[chat_id].items()
                    if datetime.fromtimestamp(last_time) > week_ago
                }
            
            data_store.save_data()
        except Exception as e:
            print(f"Ошибка при очистке статистики: {str(e)}")
        
        await asyncio.sleep(86400)  # Выполняем очистку раз в день

@app.route('/')
def home():
    return "Bot is running!"

def run_flask():
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def main():
    # Запускаем Flask в отдельном потоке
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # Запускаем поток для keep_alive
    keep_alive_thread = Thread(target=keep_alive)
    keep_alive_thread.daemon = True
    keep_alive_thread.start()
    
    # Запускаем бота
    with client:
        client.start(bot_token=bot_token)
        print("Бот успешно запущен!")
        
        # Добавляем задачу очистки статистики в event loop
        loop.create_task(cleanup_old_stats())
        
        client.run_until_disconnected()

if __name__ == '__main__':
    main()