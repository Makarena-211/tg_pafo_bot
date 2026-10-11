import os
from dataclasses import dataclass
from zoneinfo import ZoneInfo

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    tg_key: str
    apple_id: str
    apple_password: str
    google_creds_path: str
    timezone: ZoneInfo


def load_settings() -> Settings:
    timezone_name = os.getenv("TIMEZONE", "Europe/Moscow")
    return Settings(
        tg_key=_required("TG_KEY"),
        apple_id=_required("APPLE_ID"),
        apple_password=_required("APPLE_ID_KEY"),
        google_creds_path=_required("PATH_TO_GOOGLE_CREDS"),
        timezone=ZoneInfo(timezone_name),
    )


def _required(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        raise RuntimeError(f"В .env не задано {name}")
    return value
