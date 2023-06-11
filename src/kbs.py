from vkbottle import Keyboard, KeyboardButtonColor, Text, OpenLink
from typing import List


welcome_kb = (
    Keyboard(inline=True)
    .add(Text("Продолжить"), KeyboardButtonColor.POSITIVE)
    .row()
    .add(Text("⏪ Вернуться в старый чат"))
).get_json()


old_chat_conf_kb = (
    Keyboard(inline=True)
    .add(OpenLink("https://vk.com", "Перейти в чат"))
).get_json()


repeat_age_kb = (
    Keyboard(inline=True)
    .add(Text("Ввести повторно"))
).get_json()


choose_sex_kb = (
    Keyboard(inline=True)
    .add(Text("Мужской"))
    .add(Text("Женский"))
).get_json()


def main_menu_kb(sex: int, vip_status: bool):
    kb = Keyboard()
    kb.add(Text("🔍 Начать поиск"), KeyboardButtonColor.POSITIVE)

    if sex == 1 and vip_status:
        kb.add(Text("👄 Найти девушку"), KeyboardButtonColor.POSITIVE)

    kb = (
        kb.row()
        .add(Text("👤 Мой профиль"), KeyboardButtonColor.PRIMARY)
        .add(Text("👑 VIP статус"), KeyboardButtonColor.PRIMARY)
        .row()
        .add(Text("⏪ Старая версия чата"))
    )

    return kb.get_json()


def profile_kb(vip_status: bool):
    kb = (
        Keyboard(inline=True)
        .add(Text("✏ Изменить данные"))
    )

    if vip_status:
        kb.row().add(Text("Отключить VIP"), KeyboardButtonColor.NEGATIVE)

    return kb.get_json()


stop_dialog_kb = (
    Keyboard(inline=True)
    .add(Text("Нет", {"cmd": "no_stop"}), KeyboardButtonColor.POSITIVE)
    .row()
    .add(Text("Да, остановить", {"cmd": "yes_stop"}), KeyboardButtonColor.NEGATIVE)
).get_json()


reg_first_kb = (
    Keyboard(inline=True)
    .add(Text("Начать"))
).get_json()


leave_queue_kb = (
    Keyboard(inline=True)
    .add(Text("Покинуть очередь"), KeyboardButtonColor.NEGATIVE)
).get_json()


def buy_vip_kb(kb_links: List[str], is_chat = False):
    kb = Keyboard(inline=True)

    if is_chat:
        kb.add(OpenLink(kb_links[0], "1 час")).row()

    kb = (
        kb.add(OpenLink(kb_links[1], "36 часов"))
        .row()
        .add(OpenLink(kb_links[2], "1 неделя"))
        .row()
        .add(OpenLink(kb_links[3], "365 дней"))
    )

    return kb.get_json()


vip_in_chat_kb = (
    Keyboard(inline=True)
    .add(Text("Оформить"), KeyboardButtonColor.POSITIVE)
).get_json()
