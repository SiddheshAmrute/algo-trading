import requests
import time
from utils.config_loader import Config


class TelegramNotifier:
    def __init__(self, config: Config, max_retries: int = 3, retry_delay: int = 2):
        """
        Initializes the Telegram Notifier service.

        Args:
            config (Config): Config loader instance (with ENV + YAML).
            max_retries (int): Retry attempts if Telegram API fails.
            retry_delay (int): Seconds to wait between retries.
        """
        self.bot_token = config.get_env("TELEGRAM_BOT_TOKEN")
        self.chat_id = config.get_env("TELEGRAM_CHAT_ID")
        self.max_retries = max_retries
        self.retry_delay = retry_delay

        if not self.bot_token or not self.chat_id:
            raise ValueError("Telegram bot token or chat ID missing in environment variables.")

        self.url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"

    def send_message(self, message: str, parse_mode: str = "Markdown"):
        """
        Sends a text message to the specified Telegram chat.

        Args:
            message (str): Message to send.
            parse_mode (str): Format for message ('Markdown' or 'HTML').

        Returns:
            dict: Telegram API response in JSON format.
        """
        payload = {"chat_id": self.chat_id, "text": message}
        if parse_mode:
            payload["parse_mode"] = parse_mode  # only include if provided

        for attempt in range(1, self.max_retries + 1):
            try:
                response = requests.post(self.url, json=payload, timeout=10)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                if attempt < self.max_retries:
                    time.sleep(self.retry_delay)
                else:
                    raise Exception(f"Failed to send Telegram message after {self.max_retries} attempts: {e}")



from utils.config_loader import Config
# from services.telegram_notifier import TelegramNotifier

if __name__ == "__main__":
    config = Config()
    notifier = TelegramNotifier(config)

    response = notifier.send_message("🚀 Algo Trading System Started Successfully")
    print(response)
