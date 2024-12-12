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

        # Если список пуст, добавляем всех пользователей
        if not data_store.ping_list:
            for user in participants:
                if not user.bot and not user.deleted:
                    data_store.ping_list.add(user.id)

        # Формируем список упоминаний только тех, кто не отключил уведомления
        for user in participants:
            if (not user.bot and not user.deleted and 
                user.id in data_store.ping_list):
                mentions.append(f"[{user.first_name}](tg://user?id={user.id})")

        if not mentions:
            await event.respond("❌ Список пользователей для уведомлений пуст")
            return

        # Разбиваем на группы и отправляем
        mention_groups = split_list(mentions, 20)
        for group in mention_groups:
            await event.respond("🔔 Пинг!\n" + " ".join(group))
            await asyncio.sleep(2)

        # Сохраняем обновленный список
        data_store.save_data()

    except Exception as e:
        print(f"Ошибка в ping_cmd: {str(e)}")
        await event.respond("Произошла ошибка при выполнении команды")

@client.on(events.NewMessage(pattern=r'^/pingoff$'))
async def pingoff_cmd(event):
    try:
        user_id = event.sender_id
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
        if user_id not in data_store.ping_list:
            data_store.ping_list.add(user_id)
            data_store.save_data()
            await event.respond("✅ Вы включили уведомления")
        else:
            await event.respond("❌ Уведомления уже включены")
    except Exception as e:
        print(f"Ошибка в pingon_cmd: {str(e)}")
        await event.respond("Произошла ошибка при выполнении команды")

# Также добавим обработчик для новых участников
@client.on(events.ChatAction)
async def handle_user_update(event):
    try:
        if event.user_joined or event.user_added:
            user_id = event.user_id
            if user_id not in data_store.ping_list:
                data_store.ping_list.add(user_id)
                data_store.save_data()
    except Exception as e:
        print(f"Ошибка при обработке нового участника: {str(e)}")