from src import kbs
from src import texts

from src.middlewares import api_manager, cached_urls
from src.repositories import UserRepository
from src.models.user_model import User
from src.uploading.upload_cache import CacheAssistant
from src.chat_manager.cloudpayments import CloudPayments
from src.config_reader import PAY_TOKEN, API_ENDPOINT, rates
from vkbottle.bot import BotLabeler, Message, rules


bl = BotLabeler()
cache_assistant = CacheAssistant()
cloud_payments = CloudPayments(PAY_TOKEN)


async def send_vip_rates(user_id: int, user_inf: User, is_chat = False):
    curr_api = api_manager[user_id]

    if user_inf.vip_status:
        return await curr_api.messages.send(
            user_id, random_id=0, message="👑 Вип: Подключен"
        )

    if cached_urls.get(user_id) is None:
        await cloud_payments.setup(curr_api.http_client)

        group_id = (await curr_api.groups.get_by_id())[0].id

        payment_obj = [
            await curr_api.http_client.request_json(
                f"{API_ENDPOINT}/generate-url", "POST", json={
                    "amount": curr_data["amount"],
                    "description": curr_data["desc"],
                    "user_id": str(user_id),
                    "confiramtion": curr_data["confirm"],
                    "sub_id": curr_data["sub_id"],
                    "group_id": str(group_id).replace("-", "")
                }
            ) for curr_data in rates
        ]

        curr_ids = [
            curr_response["response"]["payment_id"]
            for curr_response in payment_obj
        ]

        cached_urls[user_id] = [
            f"https://comby.pro/payment?payment_id={curr_id}"
            for curr_id in curr_ids
        ]

    vip_links = cached_urls[user_id]

    res_attachment = await cache_assistant.get_photo(
        curr_api, "misc/images/vip_info.jpg"
    )

    return await curr_api.messages.send(
        user_id, random_id=0, message=texts.vip_info,
        attachment=res_attachment,
        keyboard=kbs.buy_vip_kb(vip_links, is_chat)
    )


@bl.private_message(rules.PayloadRule({"cmd": "confirm_vip"}))
async def confirm_remove_vip(message: Message):
    user_rep = UserRepository(message.from_id)
    user_inf = await user_rep.get()

    if not user_inf.vip_status:
        return "У вас отсутствует подписка"

    await cloud_payments.setup()
    await cloud_payments.method("subscriptions/cancel", {"Id": user_inf.sub_id})

    await user_rep.del_vip()

    return "Подписка успешна отключена"
