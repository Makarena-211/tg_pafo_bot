import asyncio
from datetime import datetime

from calendars.apple import fetch_apple_events
from calendars.google import fetch_google_events
from calendars.models import CalendarSnapshot
from config import Settings, load_settings


async def collect_events(
    start: datetime,
    end: datetime,
    settings: Settings | None = None,
) -> CalendarSnapshot:
    """События обоих календарей одним списком, отсортированные по началу."""
    settings = settings or load_settings()
    apple = await _safe_apple(settings, start, end)
    google = await _safe_google(settings, start, end)
    events = [*apple.events, *google.events]
    events.sort(key=lambda item: (item.start_time, item.source, item.summary))
    return CalendarSnapshot(events=events, errors=[*apple.errors, *google.errors])


async def _safe_apple(settings: Settings, start: datetime, end: datetime) -> CalendarSnapshot:
    try:
        return await fetch_apple_events(settings, start, end)
    except Exception as exc:
        return CalendarSnapshot(errors=[f"Apple: {exc}"])


async def _safe_google(settings: Settings, start: datetime, end: datetime) -> CalendarSnapshot:
    try:
        return await asyncio.to_thread(fetch_google_events, settings, start, end)
    except Exception as exc:
        return CalendarSnapshot(errors=[f"Google: {exc}"])
