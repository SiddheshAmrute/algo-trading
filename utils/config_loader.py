import os
import yaml
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path=".env")

class Config:
    def __init__(self, yaml_path="config/config.yaml"):
        self.env = self._load_env()
        self.yaml = self._load_yaml(yaml_path)

    def _load_env(self):
        return {
            # Dhan API
            "DHAN_TRADING_CLIENT_ID": os.getenv("DHAN_TRADING_CLIENT_ID"),
            "DHAN_TRADING_ACCESS_TOKEN": os.getenv("DHAN_TRADING_ACCESS_TOKEN"),
            "DHAN_DATA_CLIENT_ID": os.getenv("DHAN_DATA_CLIENT_ID"),
            "DHAN_DATA_ACCESS_TOKEN": os.getenv("DHAN_DATA_ACCESS_TOKEN"),

            # Telegram
            "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
            "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),

            # Postgres
            "POSTGRES_USER": os.getenv("POSTGRES_USER"),
            "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD"),
            "POSTGRES_DB": os.getenv("POSTGRES_DB"),
            "POSTGRES_HOST": os.getenv("POSTGRES_HOST"),
            "POSTGRES_PORT": os.getenv("POSTGRES_PORT", 5432),
        }

    def _load_yaml(self, path):
        if not os.path.exists(path):
            return {}
        with open(path, "r") as file:
            return yaml.safe_load(file)

    def get(self, section, key, default=None):
        """ Get from YAML config """
        return self.yaml.get(section, {}).get(key, default)

    def get_section(self, section, default=None):
        """ Get a full YAML section """
        return self.yaml.get(section, default or {})

    def get_env(self, key, default=None):
        """ Get from ENV config """
        return self.env.get(key, default)

    def __getitem__(self, key):
        """ Shortcut: ENV has priority, else YAML """
        return self.env.get(key) or self.yaml.get(key)


from utils.config_loader import Config
if __name__ == "__main__":
    config = Config()

    # ENV
    print("Dhan Token:", config.get_env("DHAN_TRADING_ACCESS_TOKEN"))

    # YAML key
    max_daily_loss = config.get("risk_limits", "max_daily_loss")
    print("Max Daily Loss:", max_daily_loss)

    # YAML full section
    indicators = config.get_section("indicators")
    print("Indicators:", indicators)

    # Shortcut access
    print("Postgres DB:", config["POSTGRES_DB"])
