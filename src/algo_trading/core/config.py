# File: src/algo_trading/core/config.py
"""
Central configuration loader.

- Uses pydantic.BaseSettings to pick up environment variables (and .env automatically).
- Loads config/config.yaml for defaults and non-secret settings.
- Environment variables take precedence over YAML.
- Exposes a simple Config wrapper with helper accessors.

Usage:
    from algo_trading.core.config import get_config
    cfg = get_config()
    token = cfg.get_env("DHAN_TRADING_ACCESS_TOKEN")
    risk_limits = cfg.get_section("risk_limits")
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseSettings, Field


ROOT = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT / ".env"
YAML_PATH = ROOT / "config" / "config.yaml"


class Settings(BaseSettings):
    # App
    app_env: str = Field("development", env="APP_ENV")
    debug: bool = Field(False, env="DEBUG")
    host: str = Field("0.0.0.0", env="HOST")
    port: int = Field(8000, env="PORT")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # Database
    database_url: Optional[str] = Field(None, env="DATABASE_URL")
    database_echo: bool = Field(False, env="DATABASE_ECHO")

    # Dhan (broker/data)
    dhan_base_url: Optional[str] = Field(None, env="DHAN_BASE_URL")
    dhan_trading_client_id: Optional[str] = Field(None, env="DHAN_TRADING_CLIENT_ID")
    dhan_trading_access_token: Optional[str] = Field(None, env="DHAN_TRADING_ACCESS_TOKEN")
    dhan_data_client_id: Optional[str] = Field(None, env="DHAN_DATA_CLIENT_ID")
    dhan_data_access_token: Optional[str] = Field(None, env="DHAN_DATA_ACCESS_TOKEN")
    dhan_sandbox: bool = Field(True, env="DHAN_SANDBOX")

    # Telegram
    telegram_bot_token: Optional[str] = Field(None, env="TELEGRAM_BOT_TOKEN")
    telegram_chat_id: Optional[str] = Field(None, env="TELEGRAM_CHAT_ID")

    # Secrets (generic)
    secret_key: Optional[str] = Field(None, env="SECRET_KEY")

    class Config:
        # load .env automatically (you can override or leave empty)
        env_file = str(ENV_FILE)
        env_file_encoding = "utf-8"
        case_sensitive = False


def _load_yaml(path: Path) -> Dict[str, Any]:
    """Load YAML file into a dict. Returns empty dict if file missing or invalid."""
    try:
        if not path.exists():
            return {}
        with path.open("r", encoding="utf-8") as fh:
            return yaml.safe_load(fh) or {}
    except Exception:
        # Keep failures non-fatal — settings from env should be primary source.
        return {}


class Config:
    """High-level config wrapper exposing settings + YAML.

    - env values (via pydantic Settings) have priority.
    - yaml provides defaults and more complex structured configs (risk limits, indicators).
    """

    def __init__(self, settings: Settings, yaml_config: Optional[Dict[str, Any]] = None) -> None:
        self._settings = settings
        self._yaml = yaml_config or {}

    # --- Settings (env-backed) accessors ---
    def get_env(self, key: str, default: Any = None) -> Any:
        """Return an env-backed setting by key. Keys are case-insensitive."""
        # normalize key to snake-case matching Settings attributes
        attr = key.lower()
        return getattr(self._settings, attr, default)

    def settings_dict(self) -> Dict[str, Any]:
        """Return pydantic settings as a dict (useful for logging/debugging)."""
        return self._settings.dict()

    # --- YAML accessors ---
    def get(self, section: str, key: str, default: Any = None) -> Any:
        """Return a single value from YAML section (returns default if not present)."""
        section_dict = self._yaml.get(section, {})
        if not isinstance(section_dict, dict):
            return default
        return section_dict.get(key, default)

    def get_section(self, section: str, default: Any = None) -> Any:
        """Return entire YAML section (or default)."""
        return self._yaml.get(section, default)

    # --- Combined lookup ---
    def __getitem__(self, key: str) -> Any:
        """
        Combined lookup: env first, then top-level YAML key.
        Example: cfg['dhan'] -> returns YAML 'dhan' section if env doesn't have it.
        """
        env_val = self.get_env(key)
        if env_val not in (None, "", []):
            return env_val
        return self._yaml.get(key)

    def to_dict(self) -> Dict[str, Any]:
        """Return merged view (settings + yaml) — env wins on conflicts."""
        merged = dict(self._yaml)
        merged.update({k: v for k, v in self._settings.dict().items() if v is not None})
        return merged


@lru_cache()
def get_config(yaml_path: Optional[str] = None) -> Config:
    """Return a cached Config object for the application."""
    yaml_p = Path(yaml_path) if yaml_path else YAML_PATH
    yaml_cfg = _load_yaml(yaml_p)
    settings = Settings()
    return Config(settings=settings, yaml_config=yaml_cfg)


# Convenience alias used across the codebase
get_settings = get_config


if __name__ == "__main__":
    # quick manual test
    cfg = get_config()
    print("APP ENV:", cfg.get_env("APP_ENV"))
    print("DHAN SANDBOX:", cfg.get_env("DHAN_SANDBOX"))
    print("Dhan YAML section:", cfg.get_section("dhan"))
    print("Risk limits:", cfg.get_section("risk_limits"))
