from vkbottle import Keyboard, KeyboardButtonColor, Text

welcome_kb = (
    Keyboard(inline=True)
    .add(Text("Продолжить"), KeyboardButtonColor.POSITIVE)
    .row()
    .add(Text("Вернуться в старый чат"))
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


main_menu_kb = (
    Keyboard()
    .add(Text("Начать поиск"), KeyboardButtonColor.POSITIVE)
    .row()
    .add(Text("Мой профиль"), KeyboardButtonColor.PRIMARY)
    .row()
    .add(Text("Старая версия чата"))
)


change_data_kb = (
    Keyboard(inline=True)
    .add(Text("Изменить данные"))
).get_json()


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
