from datetime import datetime

DISCLAIMER = (
    "⚠️ ВАЖНО: GRUZO — только информационная площадка-посредник. "
    "Мы не несём ответственности за качество работы, оплату, безопасность и споры между участниками."
)

RULES = f"""
📜 Правила сервиса GRUZO

1) Указывайте только правдивые данные по заказам.
2) Оплата, условия и безопасность — предмет договорённости между участниками.
3) Запрещены мошенничество, спам, оскорбления, незаконная деятельность.
4) Заказ на режимный объект должен быть явно помечен.
5) Нарушения правил = блокировка без возврата средств.

{DISCLAIMER}
""".strip()


def order_text(order, dispatcher, registered_days: int, created_count: int, recommends: int, worker_names: list[str]) -> str:
    per_person = order["rate_per_hour"] * order["hours"]
    secure = "🚨 Режимный объект — требуется паспорт для пропуска" if order["secure_object"] else "✅ Обычный объект"
    workers_line = f"👷 Нужно грузчиков: {order['workers_taken']} из {order['workers_needed']}"
    workers_joined = "\n".join([f"   • @{name}" if name and not name.startswith("@") else f"   • {name}" for name in worker_names])
    workers_block = f"\n\n👷 Взяли заказ:\n{workers_joined}" if worker_names else ""

    return (
        f"📦 Заказ #{order['id']}\n\n"
        f"🔹 Описание: {order['description']}\n"
        f"📍 Адрес: {order['address']}\n"
        f"🕒 Время: {datetime.fromisoformat(order['start_at']).strftime('%d.%m.%Y, %H:%M')}\n\n"
        f"{workers_line}\n"
        f"💰 Условия: {order['rate_per_hour']} ₽/час × {order['hours']} часа = {per_person} ₽ (на 1 человека)\n\n"
        f"{secure}\n\n"
        f"──────────────────\n"
        f"👨‍💼 Диспетчер: @{dispatcher['username'] or dispatcher['full_name']}\n"
        f"   • Зарегистрирован: {registered_days} дней назад\n"
        f"   • Создал заказов: {created_count}\n"
        f"   • Рекомендуют: {recommends} грузчиков ⭐"
        f"{workers_block}"
    )
