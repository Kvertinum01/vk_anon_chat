import json

from vkbottle import EMPTY_KEYBOARD, PhotoMessageUploader, API
from vkbottle.bot import BotLabeler, Message, rules

from src import texts
from src import kbs
from src import app

from src.repositories import UserRepository
from src.chat_manager.manager import ChatManager
from src.chat_manager.cloudpayments import CloudPayments
from src.states import UserInfo
from src.uploading.upload_manager import UploadManager
from src.uploading.upload_cache import CacheAssistant
from src.middlewares import api_manager, cached_urls
from src.config_reader import PAY_TOKEN, rates


bl = BotLabeler()
cache_assistant = CacheAssistant()
chat_manager = ChatManager("vk")
cloud_payments = CloudPayments(PAY_TOKEN)


async def send_vip_rates(user_id: int, is_chat = False):
    user_rep = UserRepository(user_id)
    user_inf = await user_rep.get()

    curr_api = api_manager[user_id]

    if user_inf.vip_status:
        return await curr_api.messages.send(
            user_id, random_id=0, message="👑 Вип: Подключен"
        )

    if cached_urls.get(user_id) is None:
        await cloud_payments.setup(curr_api.http_client)

        pay_objects = [
            await cloud_payments.method(
                "orders/create", {
                    "Amount": curr_data["amount"],
                    "Description": curr_data["desc"],
                    "AccountId": str(user_id),
                    "RequireConfirmation": curr_data["confirm"],
                    "JsonData": curr_data["json_data"],
                }
            ) for curr_data in rates
        ]
        
        cached_urls[user_id] = [curr_obj["Url"] for curr_obj in pay_objects]

    vip_links = cached_urls[user_id]

    res_text = texts.vip_info.format(extra_info="")

    if is_chat:
        res_text = texts.vip_info.format(
            extra_info="\n1 руб. - 1 час (затем списание 399 руб. раз в 2 недели)\n"
        )

    res_attachment = await cache_assistant.get_photo(
        curr_api, "misc/images/vip_info.jpg"
    )

    return await curr_api.messages.send(
        user_id, random_id=0, message=res_text,
        attachment=res_attachment,
        keyboard=kbs.buy_vip_kb(vip_links, is_chat)
    )


@bl.private_message(text=["Продолжить", "Ввести повторно", "✏ Изменить данные"])
async def continue_chat(message: Message):
    await app.bot.state_dispenser.set(message.from_id, UserInfo.AGE)
    return "Введите ваш возраст, например 18"


@bl.private_message(state=UserInfo.AGE)
async def save_user_age(message: Message):
    await app.bot.state_dispenser.delete(message.from_id)
    user_rep = UserRepository(message.from_id)
    
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


@bl.private_message(text=["⏪ Вернуться в старый чат", "⏪ Старая версия чата"])
async def back_to_old_chat(message: Message):
    return await message.answer(texts.old_chat, keyboard=kbs.old_chat_conf_kb)


@bl.private_message(text=["Мужской", "Женский"])
async def choose_sex(message: Message):
    user_rep = UserRepository(message.from_id)
    user_inf = await user_rep.get()
    curr_sex = 1 if message.text == "Мужской" else 2

    if user_inf is None:
        return "Для начала пройдите регистрацию"

    await user_rep.end_reg()
    await user_rep.update_sex(curr_sex)
    await message.answer(
        "⚡Выберите действие:",
        keyboard=kbs.main_menu_kb(curr_sex, user_inf.vip_status)
    )


@bl.private_message(text="👤 Мой профиль")
async def show_profile(message: Message):
    user_rep = UserRepository(message.from_id)
    user_inf = await user_rep.get()

    text_sex = "Мужской" if user_inf.sex == 1 else "Женский"
    text_vip = "Подключен" if user_inf.vip_status else "Отсутствует"

    await message.answer(texts.profile_text.format(
        sex=text_sex, age=user_inf.age,
        created_at=user_inf.created_at.strftime("%d.%m.%Y"),
        vip_status=text_vip,
    ), keyboard=kbs.profile_kb(user_inf.vip_status))


@bl.private_message(text="Отключить VIP")
async def remove_vip(message: Message):
    user_rep = UserRepository(message.from_id)
    user_inf = await user_rep.get()

    if not user_inf.vip_status:
        return "У вас отсутствует подписка"

    await cloud_payments.setup()
    await cloud_payments.method("subscriptions/cancel", {"Id": user_inf.sub_id})

    await user_rep.del_vip()

    return "Подписка успешна отключена"


@bl.private_message(text=["🔍 Начать поиск", "👄 Найти девушку"])
async def find_companion(message: Message):
    if chat_manager.check_active_chats(message.from_id):
        return "Вы уже в чате"

    if chat_manager.check_queue(message.from_id):
        return "Вы уже в очереди"

    sex_prefer = None
    user_inf = await UserRepository(message.from_id).get()

    if message.text in ["👄 Найти девушку"] and user_inf.vip_status:
        sex_prefer = 2 if user_inf.sex == 1 else 1

    curr_user = await chat_manager.find_companion(message.from_id, sex_prefer)
    
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

    chat_user_inf = await UserRepository(chat_user_id).get()
    curr_user_inf = await UserRepository(message.from_id).get()

    await message.answer(
        "✅ Вы закончили диалог",
        keyboard=kbs.main_menu_kb(chat_user_inf.sex, curr_user_inf.vip_status)
    )

    await api_manager[chat_user_id].messages.send(
        chat_user_id, message="❗Собеседник закончил диалог",
        keyboard=kbs.main_menu_kb(chat_user_inf.sex, curr_user_inf.vip_status),
        random_id=0
    )


@bl.private_message(rules.CommandRule("новый", ["!", "/"]))
async def new_chat(message: Message):
    await stop_dialog(message)
    await find_companion(message)


@bl.private_message(text="👑 VIP статус")
async def vip_info(message: Message):
    await send_vip_rates(message.from_id)


@bl.private_message(text="Оформить")
async def vip_info(message: Message):
    if not chat_manager.check_active_chats(message.from_id):
        return "Функция доступна только в диалоге с пользователем"

    await send_vip_rates(message.from_id, True)


@bl.private_message()
async def on_all(message: Message):
    curr_user_inf = await UserRepository(message.from_id).get()

    if not chat_manager.check_active_chats(message.from_id):
        return await message.answer(
            texts.unk_command,
            keyboard=kbs.main_menu_kb(curr_user_inf.sex, curr_user_inf.vip_status)
        )
    
    chat_user_id = chat_manager.get_active_user(message.from_id)
    attachments = []

    chat_user_inf = await UserRepository(chat_user_id).get()

    curr_vip_status = chat_user_inf.vip_status or curr_user_inf.vip_status

    for curr_attachment in message.attachments:
        attach_type = curr_attachment.type.value

        upload_manager = UploadManager(message.ctx_api, message.peer_id)

        if not upload_manager.check_document(attach_type):
            continue

        match attach_type:
            case "photo":
                if not curr_vip_status:
                    await message.answer(
                        "Чтобы обмениваться фото с собеседником, подключи VIP тариф",
                        keyboard=kbs.vip_in_chat_kb
                    )
                    return await api_manager[chat_user_id].messages.send(
                        chat_user_id, random_id=0,
                        message="Собеседник отправил вам фото. "
                        "Разблокируйте возможность просмотра и обмена фотографиями.",
                        keyboard=kbs.vip_in_chat_kb
                    )

                res_string = await upload_manager.get_attachment(
                    attach_type, curr_attachment.photo.sizes[-1].url,
                )

            case "audio_message":
                if not curr_vip_status:
                    await message.answer(
                        "Голосовые могут отправлять только VIP юзеры",
                        keyboard=kbs.vip_in_chat_kb
                    )
                    return await api_manager[chat_user_id].messages.send(
                        chat_user_id, random_id=0,
                        message="Собеседник пытался отправить вам голосовое. "
                        "Оформите VIP статус и обменивайтесь голосовыми.",
                        keyboard=kbs.vip_in_chat_kb
                    )

                res_string = await upload_manager.get_attachment(
                    attach_type, curr_attachment.audio_message.link_ogg,
                    title="voice_message",
                )

            case "video":
                if not curr_vip_status:
                    await message.answer(
                        "Отправка видео ограниченна! Оплатите VIP тариф.",
                        keyboard=kbs.vip_in_chat_kb
                    )
                    return await api_manager[chat_user_id].messages.send(
                        chat_user_id, random_id=0,
                        message="Собеседник пытался отправить вам видео. "
                        "Разблокируйте возможность просмотра и обмена видео.",
                        keyboard=kbs.vip_in_chat_kb
                    )

                res_string = f"video{curr_attachment.video.owner_id}_{curr_attachment.video.id}"

            case _:
                continue

        attachments.append(res_string)

    await message.ctx_api.messages.mark_as_read(peer_id=message.peer_id)

    await api_manager[chat_user_id].messages.send(
        chat_user_id, message=message.text,
        attachment=",".join(attachments),
        random_id=0
    )
