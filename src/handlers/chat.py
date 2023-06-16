import cv2
import numpy

from src import kbs
from src import texts

from src.chat_manager.manager import ChatManager
from src.models.user_model import User
from src.repositories import UserRepository
from src.middlewares import api_manager
from src.uploading.upload_manager import UploadManager
from src.handlers.vip import send_vip_rates

from vkbottle import EMPTY_KEYBOARD
from vkbottle.bot import BotLabeler, Message, rules


chat_manager = ChatManager("vk")
bl = BotLabeler()


@bl.private_message(text="Оформить")
async def vip_info(message: Message, user_inf: User):
    if not chat_manager.check_active_chats(message.from_id):
        return "Функция доступна только в диалоге с пользователем"

    await send_vip_rates(message.from_id, user_inf, True)


@bl.private_message(text=["🔍 Начать поиск", "👄 Найти девушку", "💪 Найти мужчину"])
async def find_companion(message: Message):
    if chat_manager.check_active_chats(message.from_id):
        return "Вы уже в чате"

    if chat_manager.check_queue(message.from_id):
        return "Вы уже в очереди"
    
    user_inf = await UserRepository(message.from_id).get()

    if chat_manager.check_daily_chats(message.from_id, user_inf.vip_status):
        return await message.answer(
            texts.dialog_limit, keyboard=kbs.check_price_kb,
        )
    
    sex_prefer = None

    if message.text in ["👄 Найти девушку", "💪 Найти мужчину"]:
        if user_inf.vip_status:
            sex_prefer = 2 if user_inf.sex == 1 else 1
        else:
            return await message.answer(
                "Поиск по полу доступен только VIP пользователям",
                keyboard=kbs.check_price_kb
            )

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


@bl.private_message(rules.PayloadRule({"cmd": "yes_stop"}))
async def stop_dialog(message: Message):
    if not chat_manager.check_active_chats(message.from_id):
        return "У вас нет активных чатов"
    
    chat_user_id = chat_manager.get_active_user(message.from_id)
    chat_manager.remove_active_chat(message.from_id)

    curr_user_inf = await UserRepository(message.from_id).get()
    chat_user_inf = await UserRepository(chat_user_id).get()

    await message.answer(
        "✅ Вы закончили диалог",
        keyboard=kbs.main_menu_kb(curr_user_inf.sex)
    )

    await api_manager[chat_user_id].messages.send(
        chat_user_id, message="❗Собеседник закончил диалог",
        keyboard=kbs.main_menu_kb(chat_user_inf.sex),
        random_id=0
    )


@bl.private_message(rules.CommandRule("новый", ["!", "/"]))
async def new_chat(message: Message):
    await stop_dialog(message)
    await find_companion(message)


@bl.private_message()
async def on_all(message: Message):
    curr_user_inf = await UserRepository(message.from_id).get()

    if not chat_manager.check_active_chats(message.from_id):
        return await message.answer(
            texts.unk_command,
            keyboard=kbs.main_menu_kb(curr_user_inf.sex)
        )
    
    chat_user_id = chat_manager.get_active_user(message.from_id)
    attachments = []

    chat_user_inf = await UserRepository(chat_user_id).get()

    curr_vip_status = chat_user_inf.vip_status or curr_user_inf.vip_status

    for curr_attachment in message.attachments:
        attach_type = curr_attachment.type.value

        upload_manager = UploadManager(api_manager[chat_user_id], message.peer_id)

        if not upload_manager.check_document(attach_type):
            continue

        match attach_type:
            case "photo":
                doc_bytes = await upload_manager.get_bytes(curr_attachment.photo.sizes[-1].url)

                if not curr_vip_status:
                    await message.answer(
                        "Чтобы обмениваться фото с собеседником, подключи VIP тариф",
                        keyboard=kbs.vip_in_chat_kb
                    )

                    np_image = numpy.asarray(bytearray(doc_bytes), dtype="uint8")
                    cv2_image = cv2.imdecode(np_image, cv2.IMREAD_COLOR)

                    blured_image = cv2.blur(cv2_image, (40, 40))
                    img_bytes = cv2.imencode(".png", blured_image)[1].tobytes()

                    curr_img = await upload_manager.get_by_bytes("photo", img_bytes)

                    return await api_manager[chat_user_id].messages.send(
                        chat_user_id, random_id=0,
                        message="Собеседник отправил вам фото. "
                        "Разблокируйте возможность просмотра и обмена фотографиями.",
                        keyboard=kbs.vip_in_chat_kb,
                        attachment=curr_img,
                    )

                res_string = await upload_manager.get_by_bytes(
                    attach_type, doc_bytes
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

    ignore_texts = ["👤", "👑", "🔍", "💬"]
    res_text = message.text

    for curr_ignore in ignore_texts:
        res_text = res_text.replace(curr_ignore, "")

    if not res_text and message.text != "":
        return

    await api_manager[chat_user_id].messages.send(
        chat_user_id, message=res_text,
        attachment=",".join(attachments),
        random_id=0
    )
