from vkbottle.bot import BotLabeler, Message, rules

from src import texts
from src import kbs
from src import app

from src.repositories import UserRepository
from src.models.user_model import User
from src.states import UserInfo
from src.handlers.vip import send_vip_rates, end_vip

from datetime import datetime

bl = BotLabeler()


@bl.private_message(text=["Продолжить", "✏ Изменить данные"])
async def continue_chat(message: Message):
    await message.answer("Укажите ваш пол", keyboard=kbs.choose_sex_kb)


@bl.private_message(text="Ввести повторно")
async def repeat_age(message: Message):
    await app.bot.state_dispenser.set(message.from_id, UserInfo.AGE)
    return "✏ Введите ваш возраст, чтобы мы подбирали для вас максимально подходящих собеседников"


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
        return "Для начала пройдите регистрацию"

    user_inf = await user_rep.get()

    await user_rep.end_reg()
    await message.answer(
        "⚡Выберите действие:",
        keyboard=kbs.main_menu_kb(user_inf.sex)
    )


@bl.private_message(text="Начать")
async def start_bot(message: Message):
    await message.answer(
        texts.start_bot,
        keyboard=kbs.welcome_kb,
        dont_parse_links=True,
    )


@bl.private_message(text=["⏪ Вернуться в старый чат", "⏪ Старая версия чата"])
async def back_to_old_chat(message: Message):
    return await message.answer(texts.old_chat, keyboard=kbs.old_chat_conf_kb)


@bl.private_message(
    rules.PayloadRule([{"cmd": "set_male"}, {"cmd": "set_female"}])
)
async def choose_sex(message: Message):
    user_rep = UserRepository(message.from_id)
    curr_sex = 1 if message.text == "Мужской" else 2

    if not await user_rep.get():
        await user_rep.new(20)

    await app.bot.state_dispenser.set(message.from_id, UserInfo.AGE)

    await user_rep.update_sex(curr_sex)
    return "✏ Введите ваш возраст, чтобы мы подбирали для вас максимально подходящих собеседников"


@bl.private_message(text="👤 Мой профиль")
async def show_profile(message: Message, user_inf: User):
    text_sex = "Мужской" if user_inf.sex == 1 else "Женский"
    text_vip = "Подключен" if user_inf.vip_status else "Отсутствует"

    await message.answer(texts.profile_text.format(
        sex=text_sex, age=user_inf.age,
        created_at=user_inf.created_at.strftime("%d.%m.%Y"),
        vip_status=text_vip,
    ), keyboard=kbs.profile_kb())


@bl.private_message(rules.CommandRule("подписки", ["!", "/"]))
async def remove_vip(message: Message, user_inf: User):
    if not user_inf.vip_status:
        return "У вас отсутствует подписка"
    
    return await message.answer(
        "Вы уверены, что хотетие отключить подписку?",
        keyboard=kbs.confirm_disable_vip_kb
    )


@bl.private_message(rules.PayloadRule({"cmd": "confirm_vip"}))
async def confirm_vip(message: Message):
    confirm_res = await end_vip(message.from_id)

    if not confirm_res:
        return "У вас отсутствует VIP"
    
    user_rep = UserRepository(message.from_id)
    user_inf = await user_rep.get()

    await message.answer(
        "Подписка успешно отключена",
        keyboard=kbs.main_menu_kb(user_inf.sex)
    )


@bl.private_message(rules.PayloadRule({"cmd": "continue_vip"}))
async def continue_vip(message: Message):
    user_rep = UserRepository(message.from_id)
    user_inf = await user_rep.get()

    await message.answer(
        "⚡Выберите действие:",
        keyboard=kbs.main_menu_kb(user_inf.sex)
    )


@bl.private_message(text="⛔ Остановить диалог")
@bl.private_message(rules.CommandRule("стоп", ["!", "/"]))
async def pre_stop_chat(message: Message):
    return await message.answer(texts.stop_dialog, keyboard=kbs.stop_dialog_kb)


@bl.private_message(rules.PayloadRule({"cmd": "no_stop"}))
async def continue_dialog(_):
    return "Продолжайте общение"


@bl.private_message(rules.CommandRule("вип", ["!", "/"]))
@bl.private_message(text=["👑 VIP статус", "Тарифы"])
async def vip_info(message: Message, user_inf: User):
    await send_vip_rates(message.from_id, user_inf)


@bl.private_message("!endvip")
async def end_vip_inf(message: Message, user_inf: User):
    await message.answer(user_inf.exp_vip.strftime("%Y-%m-%dT%H:%M:%S"))

@bl.private_message("!setvip")
async def set_vip(message: Message):
    user_rep = UserRepository(message.from_id)
    await user_rep.set_exp(datetime.now())
