from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from calendars.models import CalendarEvent, CalendarSnapshot
from calendars.service import collect_events
from config import load_settings

router = Router()
WINDOW_DAYS = 7


@router.message(Command("upcoming"))
async def upcoming(message: Message) -> None:
    settings = load_settings()
    start = datetime.now(settings.timezone)
    end = start + timedelta(days=WINDOW_DAYS)
    snapshot = await collect_events(start, end, settings)
    for part in render_snapshot(snapshot, WINDOW_DAYS):
        await message.answer(part)


def render_snapshot(snapshot: CalendarSnapshot, days: int) -> list[str]:
    if snapshot.events:
        body = "\n\n".join(format_event(event) for event in snapshot.events)
        text = f"События на {days} дн.\n\n{body}"
    else:
        text = f"На ближайшие {days} дн. событий нет."
    if snapshot.errors:
        text += "\n\nНе удалось прочитать:\n" + "\n".join(snapshot.errors)
    return _split(text)


def format_event(event: CalendarEvent) -> str:
    source = "Apple" if event.source == "apple" else "Google"
    if event.all_day:
        when = f"{event.start_time:%d.%m.%Y}, весь день"
    else:
        when = (
            f"{event.start_time:%d.%m.%Y %H:%M}"
            f"–{event.stop_time:%H:%M} ({event.duration})"
        )
    return f"{when}\n{event.summary}\n{source} · {event.calendar_name}"


def _split(text: str, limit: int = 4000) -> list[str]:
    blocks = text.split("\n\n")
    chunks: list[str] = []
    current = ""
    for block in blocks:
        candidate = block if not current else f"{current}\n\n{block}"
        if current and len(candidate) > limit:
            chunks.append(current)
            current = block
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
