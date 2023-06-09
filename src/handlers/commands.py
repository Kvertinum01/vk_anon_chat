from vkbottle import EMPTY_KEYBOARD
from vkbottle.bot import BotLabeler, Message, rules

from src import texts
from src import kbs
from src import app

from src.repositories import UserRepository
from src.chat_manager.manager import ChatManager
from src.states import UserInfo
from src.upload_manager import UploadManager
from src.middlewares import api_manager


bl = BotLabeler()
chat_manager = ChatManager()


@bl.private_message(text=["Продолжить", "Ввести повторно", "Изменить данные"])
async def continue_chat(message: Message):
    await app.bot.state_dispenser.set(message.from_id, UserInfo.AGE)
    return "Введите ваш возраст, например 18"


@bl.private_message(state=UserInfo.AGE)
async def save_user_age(message: Message):
    user_rep = UserRepository(message.from_id)
    await app.bot.state_dispenser.delete(message.from_id)
    
    if not message.text.isdigit():
        return await message.answer(
            "Напишите число",
            keyboard=kbs.repeat_age_kb
        )
    
    if int(message.text) < 16:
        return await message.answer(
            "Сервис доступен только лицам старше 16 лет",
            keyboard=kbs.repeat_age_kb
        )
    
    if int(message.text) > 100:
        return await message.answer(
            "Укажите настоящий возраст",
            keyboard=kbs.repeat_age_kb
        )
    
    if await user_rep.get() is not None:
        await user_rep.update_age(int(message.text))
    else:
        await user_rep.new(int(message.text))

    await message.answer("Введите ваш пол", keyboard=kbs.choose_sex_kb)


@bl.private_message(text="Начать")
async def start_bot(message: Message):
    await message.answer(texts.start_bot, keyboard=kbs.welcome_kb)


@bl.private_message(text=["Вернуться в старый чат", "Старая версия чата"])
async def back_to_old_chat(_):
    return texts.old_chat


@bl.private_message(text=["Мужской", "Женский"])
async def choose_sex(message: Message):
    user_rep = UserRepository(message.from_id)
    curr_sex = 1 if message.text == "Мужской" else 2

    if user_rep.get() is None:
        return "Для начала пройдите регистрацию"

    await user_rep.end_reg()
    await user_rep.update_sex(curr_sex)
    await message.answer("⚡Выберите действие:", keyboard=kbs.main_menu_kb)


@bl.private_message(text="Мой профиль")
async def show_profile(message: Message):
    user_rep = UserRepository(message.from_id)
    user_inf = await user_rep.get()

    text_sex = "Мужской" if user_inf.sex == 1 else "Женский"

    await message.answer(texts.profile_text.format(
        sex=text_sex, age=user_inf.age,
        created_at=user_inf.created_at.strftime("%d.%m.%Y")
    ), keyboard=kbs.change_data_kb)


@bl.private_message(text="Начать поиск")
async def find_companion(message: Message):
    if chat_manager.check_queue(message.from_id):
        return "Вы уже в очереди"

    curr_user = await chat_manager.find_companion(message.from_id)
    
    if not curr_user:
        return await message.answer(
            "Вы в очереди на поиск собеседника. Ожидайте",
            keyboard=kbs.leave_queue_kb
        )
    
    await message.answer(texts.got_companion, keyboard=EMPTY_KEYBOARD)
    await api_manager[curr_user.id].messages.send(
        curr_user.id, message=texts.got_companion,
        keyboard=EMPTY_KEYBOARD, random_id=0
    )


@bl.private_message(text="Покинуть очередь")
async def leave_queue(message: Message):
    leave_res = chat_manager.leave_queue(message.from_id)

    if not leave_res:
        return "Вы не в очереди"
    
    return "Вы покинули очередь"


@bl.private_message(rules.CommandRule("стоп", ["!", "/"]))
async def pre_stop_chat(message: Message):
    return await message.answer(texts.stop_dialog, keyboard=kbs.stop_dialog_kb)


@bl.private_message(rules.PayloadRule({"cmd": "no_stop"}))
async def continue_dialog(_):
    return "Продолжайте общение"


@bl.private_message(rules.PayloadRule({"cmd": "yes_stop"}))
async def stop_dialog(message: Message):
    if not chat_manager.check_active_chats(message.from_id):
        return "У вас нет активных чатов"
    
    chat_user_id = chat_manager.get_active_user(message.from_id)
    chat_manager.remove_active_chat(message.from_id)

    await api_manager[chat_user_id].messages.send(
        chat_user_id, message="Собеседник закончил диалог",
        keyboard=kbs.main_menu_kb, random_id=0
    )

    return await message.answer("✅ Вы закончили диалог", keyboard=kbs.main_menu_kb)


@bl.private_message(rules.CommandRule("новый", ["!", "/"]))
async def new_chat(message: Message):
    await stop_dialog(message)
    await find_companion(message)


@bl.private_message()
async def on_all(message: Message):
    if not chat_manager.check_active_chats(message.from_id):
        return await message.answer(texts.unk_command, keyboard=kbs.main_menu_kb)
    
    chat_user_id = chat_manager.get_active_user(message.from_id)
    attachments = []
    curr_sticker = None

    for curr_attachment in message.attachments:
        attach_type = curr_attachment.type.value
        if attach_type == "sticker":
            curr_sticker = curr_attachment.sticker.sticker_id
            continue

        upload_manager = UploadManager(message.ctx_api)

        if not upload_manager.check_document(attach_type):
            continue

        elif attach_type == "photo":
            res_string = await upload_manager.get_attachment(
                attach_type, curr_attachment.photo.sizes[-1].url,
                peer_id=message.peer_id
            )

        elif attach_type == "audio_message":
            res_string = await upload_manager.get_attachment(
                attach_type, curr_attachment.audio_message.link_ogg,
                title="voice_message",
                peer_id=message.peer_id
            )

        elif attach_type == "doc":
            res_string = await upload_manager.get_attachment(
                attach_type, curr_attachment.doc.url,
                title="document",
                peer_id=message.peer_id
            )

        elif attach_type == "audio":
            res_string = f"audio{curr_attachment.audio.owner_id}_{curr_attachment.audio.id}"

        attachments.append(res_string)

    await api_manager[chat_user_id].messages.send(
        chat_user_id, message=message.text,
        attachment=",".join(attachments), sticker_id=curr_sticker,
        random_id=0
    )

    await message.ctx_api.messages.mark_as_read(peer_id=message.peer_id)
