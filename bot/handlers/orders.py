from datetime import datetime
from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, CallbackQuery

from bot.db import Database
from bot.keyboards import secure_object_kb, take_order_kb
from bot.texts import order_text

router = Router()


class CreateOrder(StatesGroup):
    description = State()
    address = State()
    datetime_value = State()
    workers = State()
    rate = State()
    hours = State()
    secure = State()


@router.message(F.text == "📦 Заказы")
async def open_orders(message: Message, db: Database, state: FSMContext):
    user = await db.get_user(message.from_user.id)
    if not user or not user["accepted_rules"]:
        await message.answer("Сначала завершите регистрацию через /start")
        return

    if user["role"] != "dispatcher":
        await message.answer("Для грузчика раздел заказов работает через публикации в группе.")
        return

    orders_month = await db.count_dispatcher_orders_current_month(message.from_user.id)
    premium_until = datetime.fromisoformat(user["premium_until"])
    is_premium = premium_until > datetime.utcnow()
    if not is_premium and orders_month >= 15:
        await message.answer("Лимит бесплатного тарифа: 15 заказов в месяц. Продлите подписку.")
        return

    await state.set_state(CreateOrder.description)
    await message.answer("Введите описание работы:")


@router.message(CreateOrder.description)
async def order_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(CreateOrder.address)
    await message.answer("Укажите адрес или отправьте геопозицию.")


@router.message(CreateOrder.address, F.location)
async def order_address_geo(message: Message, state: FSMContext):
    loc = message.location
    await state.update_data(address=f"Геопозиция: {loc.latitude},{loc.longitude}", geo_lat=loc.latitude, geo_lon=loc.longitude)
    await state.set_state(CreateOrder.datetime_value)
    await message.answer("Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ")


@router.message(CreateOrder.address)
async def order_address_text(message: Message, state: FSMContext):
    await state.update_data(address=message.text)
    await state.set_state(CreateOrder.datetime_value)
    await message.answer("Введите дату и время в формате ДД.ММ.ГГГГ ЧЧ:ММ")


@router.message(CreateOrder.datetime_value)
async def order_datetime(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text, "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("Неверный формат. Пример: 05.04.2026 10:00")
        return
    await state.update_data(start_at=dt.isoformat())
    await state.set_state(CreateOrder.workers)
    await message.answer("Сколько требуется грузчиков?")


@router.message(CreateOrder.workers)
async def order_workers(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 1:
        await message.answer("Введите целое число больше 0")
        return
    await state.update_data(workers_needed=int(message.text))
    await state.set_state(CreateOrder.rate)
    await message.answer("Ставка за час (₽):")


@router.message(CreateOrder.rate)
async def order_rate(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 100:
        await message.answer("Введите корректную ставку (например 400)")
        return
    await state.update_data(rate_per_hour=int(message.text))
    await state.set_state(CreateOrder.hours)
    await message.answer("Количество часов (минимум 4):")


@router.message(CreateOrder.hours)
async def order_hours(message: Message, state: FSMContext):
    if not message.text.isdigit() or int(message.text) < 4:
        await message.answer("Минимум 4 часа")
        return

    hours = int(message.text)
    data = await state.get_data()
    per_person = data["rate_per_hour"] * hours
    total = per_person * data["workers_needed"]
    await state.update_data(hours=hours)
    await state.set_state(CreateOrder.secure)
    await message.answer(
        f"Расчёт: {data['rate_per_hour']} ₽/час × {hours} часа = {per_person} ₽ (1 чел.)\n"
        f"Общая сумма: {total} ₽\n\n"
        "Это режимный объект?",
        reply_markup=secure_object_kb(),
    )


@router.message(CreateOrder.secure, F.text.in_({"✅ Да", "❌ Нет"}))
async def order_secure(message: Message, state: FSMContext, db: Database, group_chat_id: int):
    data = await state.get_data()
    data["secure_object"] = message.text == "✅ Да"
    data["dispatcher_id"] = message.from_user.id
    order_id = await db.create_order(data)
    order = await db.get_order(order_id)
    dispatcher = await db.get_user(message.from_user.id)
    created, _ = await db.get_dispatcher_stats(message.from_user.id)
    reg_days = (datetime.utcnow() - datetime.fromisoformat(dispatcher["registered_at"])).days
    text = order_text(order, dispatcher, reg_days, created, dispatcher["recommends"], [])

    if db and order and order_id:
        if hasattr(message.bot, "send_message"):
            group_message = await message.bot.send_message(
                chat_id=group_chat_id,
                text=text,
                reply_markup=take_order_kb(order_id),
            )
            await db.set_order_message_id(order_id, group_message.message_id)

    await message.answer(f"✅ Заказ #{order_id} создан и опубликован в группе.")
    await state.clear()


@router.callback_query(F.data.startswith("take_order:"))
async def take_order(callback: CallbackQuery, db: Database):
    order_id = int(callback.data.split(":", 1)[1])
    user = await db.get_user(callback.from_user.id)
    if not user or user["role"] != "worker":
        await callback.answer("Только грузчик может взять заказ", show_alert=True)
        return

    ok = await db.take_order(order_id, callback.from_user.id)
    if not ok:
        await callback.answer("Заказ уже закрыт или вы уже в нём")
        return

    order = await db.get_order(order_id)
    dispatcher = await db.get_user(order["dispatcher_id"])
    created, _ = await db.get_dispatcher_stats(order["dispatcher_id"])
    reg_days = (datetime.utcnow() - datetime.fromisoformat(dispatcher["registered_at"])).days
    worker_names = await db.get_worker_names(order_id)
    text = order_text(order, dispatcher, reg_days, created, dispatcher["recommends"], worker_names)

    await callback.message.edit_text(text=text, reply_markup=take_order_kb(order_id) if order["status"] == "open" else None)
    await callback.answer("Вы взяли заказ")
