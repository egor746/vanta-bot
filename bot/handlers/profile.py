from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message

from bot.db import Database
from bot.texts import DISCLAIMER

router = Router()


@router.message(F.text == "👤 Профиль")
async def profile(message: Message, db: Database):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Начните с /start")
        return

    created, completed = await db.get_dispatcher_stats(message.from_user.id)
    reg_days = (datetime.utcnow() - datetime.fromisoformat(user["registered_at"])).days
    premium_until = datetime.fromisoformat(user["premium_until"])
    premium_left = max((premium_until - datetime.utcnow()).days, 0)

    await message.answer(
        f"👤 Профиль\n\n"
        f"Роль: {'Диспетчер' if user['role'] == 'dispatcher' else 'Грузчик'}\n"
        f"Рейтинг: {user['rating']} ⭐\n"
        f"Зарегистрирован: {reg_days} дней назад\n"
        f"Создал заказов: {created}\n"
        f"Выполнил заказов: {completed}\n"
        f"Рекомендуют: {user['recommends']} человек\n"
        f"Premium осталось: {premium_left} дней\n\n"
        f"{DISCLAIMER}"
    )


@router.message(F.text == "📊 Мои заказы")
async def my_orders(message: Message, db: Database):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Начните с /start")
        return

    created, completed = await db.get_dispatcher_stats(message.from_user.id)
    await message.answer(f"📊 Статистика заказов\nСоздано: {created}\nВзято/выполнено: {completed}")


@router.message(F.text == "💳 Подписка / Продлить подписку")
async def subscription(message: Message, db: Database):
    user = await db.get_user(message.from_user.id)
    if not user:
        await message.answer("Начните с /start")
        return

    premium_until = datetime.fromisoformat(user["premium_until"])
    active = premium_until > datetime.utcnow()
    await message.answer(
        "💳 Подписка\n"
        "• 30 дней бесплатно после регистрации\n"
        "• Далее: 99 ₽ / месяц\n"
        "• VIP/Срочный заказ: 50 ₽\n\n"
        f"Текущий статус: {'Premium активен' if active else 'Бесплатный тариф'}\n"
        "Для подключения YooKassa задайте SHOP_ID/SECRET_KEY и реализуйте платёжный webhook."
    )
