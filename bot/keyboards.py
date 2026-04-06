from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def roles_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="👷 Грузчик"), KeyboardButton(text="👨‍💼 Диспетчер")]],
        resize_keyboard=True,
    )


def rules_kb(role: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Я ознакомлен и полностью согласен с правилами", callback_data=f"accept_rules:{role}")]]
    )


def main_menu() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="📦 Заказы"), KeyboardButton(text="👤 Профиль")],
            [KeyboardButton(text="📊 Мои заказы"), KeyboardButton(text="💳 Подписка / Продлить подписку")],
            [KeyboardButton(text="ℹ️ Помощь")],
        ],
        resize_keyboard=True,
    )


def secure_object_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="✅ Да"), KeyboardButton(text="❌ Нет")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def take_order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Взять заказ", callback_data=f"take_order:{order_id}")]]
    )


def help_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📜 Правила сервиса")]],
        resize_keyboard=True,
    )


def profile_role_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="Сменить на 👷 Грузчик", callback_data="set_role:worker")],
            [InlineKeyboardButton(text="Сменить на 👨‍💼 Диспетчер", callback_data="set_role:dispatcher")],
        ]
    )


def complete_order_kb(order_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[[InlineKeyboardButton(text="✅ Завершить заказ", callback_data=f"complete_order:{order_id}")]]
    )


def recommend_worker_kb(order_id: int, worker_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✅ Рекомендую", callback_data=f"recommend:{order_id}:{worker_id}:5")],
            [InlineKeyboardButton(text="⭐ Оценка 4", callback_data=f"recommend:{order_id}:{worker_id}:4")],
        ]
    )
