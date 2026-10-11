from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, computed_field


class CalendarEvent(BaseModel):
    """Одно событие независимо от того, пришло оно из Apple или Google."""

    id: str
    source: Literal["apple", "google"]
    calendar_name: str
    calendar_id: str
    summary: str
    start_time: datetime
    stop_time: datetime
    all_day: bool = False

    @computed_field
    @property
    def duration(self) -> str:
        minutes = int((self.stop_time - self.start_time).total_seconds() // 60)
        if minutes <= 0:
            return "0 мин"
        days, rest = divmod(minutes, 24 * 60)
        hours, mins = divmod(rest, 60)
        parts: list[str] = []
        if days:
            parts.append(f"{days} д")
        if hours:
            parts.append(f"{hours} ч")
        if mins:
            parts.append(f"{mins} мин")
        return " ".join(parts)


class CalendarSnapshot(BaseModel):
    events: list[CalendarEvent] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
