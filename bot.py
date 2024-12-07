from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins
import asyncio
import os

# Получаем данные из переменных окружения
api_id = os.environ.get('API_ID')
api_hash = os.environ.get('API_HASH')
bot_token = os.environ.get('BOT_TOKEN')

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
    await event.respond("📢 Внимание!\n" + " ".join(mentions))

# Запускаем бота
client.run_until_disconnected()