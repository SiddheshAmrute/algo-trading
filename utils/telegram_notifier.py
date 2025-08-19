import requests
from utils.config_loader import Config

config = Config()

TELEGRAM_BOT_TOKEN = config.get_env("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = config.get_env("TELEGRAM_CHAT_ID")


def send_telegram_message(message: str, parse_mode: str = "Markdown"):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        raise ValueError("Telegram token or chat ID not found in environment variables.")

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message
    }

    if parse_mode:
        payload["parse_mode"] = parse_mode  # ✅ only include if not None

    response = requests.post(url, json=payload)
    if not response.ok:
        raise Exception(f"Failed to send Telegram message: {response.text}")
    return response.json()
