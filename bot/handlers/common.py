from datetime import datetime
from aiogram import Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from bot.db import Database
from bot.keyboards import roles_kb, rules_kb, main_menu, help_kb
from bot.texts import RULES, DISCLAIMER

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, db: Database):
    await db.upsert_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(
        "Добро пожаловать в GRUZO! Выберите вашу роль:",
        reply_markup=roles_kb(),
    )


@router.message(F.text.in_({"👷 Грузчик", "👨‍💼 Диспетчер"}))
async def choose_role(message: Message):
    role = "worker" if message.text == "👷 Грузчик" else "dispatcher"
    await message.answer(RULES, reply_markup=rules_kb(role))


@router.callback_query(F.data.startswith("accept_rules:"))
async def accept_rules(callback: CallbackQuery, db: Database):
    role = callback.data.split(":", 1)[1]
    await db.set_role_and_rules(callback.from_user.id, role)
    until = (datetime.utcnow().date()).strftime('%d.%m.%Y')
    await callback.message.answer(
        f"✅ Регистрация завершена. Вам начислен premium на 30 дней с {until}.\n\n{DISCLAIMER}",
        reply_markup=main_menu(),
    )
    await callback.answer("Готово")


@router.message(F.text == "ℹ️ Помощь")
async def help_handler(message: Message):
    await message.answer("Раздел помощи. Откройте правила сервиса:", reply_markup=help_kb())


@router.message(F.text == "📜 Правила сервиса")
async def rules_handler(message: Message):
    await message.answer(RULES)
