from dataclasses import dataclass
import os
from dotenv import load_dotenv


load_dotenv()


@dataclass
class Settings:
    bot_token: str
    group_chat_id: int
    yookassa_shop_id: str
    yookassa_secret_key: str


def load_settings() -> Settings:
    token = os.getenv("BOT_TOKEN", "")
    if not token:
        raise RuntimeError("Переменная BOT_TOKEN не задана")

    return Settings(
        bot_token=token,
        group_chat_id=int(os.getenv("GROUP_CHAT_ID", "0")),
        yookassa_shop_id=os.getenv("YOOKASSA_SHOP_ID", ""),
        yookassa_secret_key=os.getenv("YOOKASSA_SECRET_KEY", ""),
    )
