import inspect
import socket
from datetime import datetime

from caldav import aio

from calendars.models import CalendarEvent, CalendarSnapshot
from calendars.normalize import event_from_apple
from config import Settings


async def fetch_apple_events(
    settings: Settings,
    start: datetime,
    end: datetime,
) -> CalendarSnapshot:
    """События iCloud за интервал [start, end) в общем формате."""
    original_getaddrinfo = socket.getaddrinfo
    socket.getaddrinfo = _ipv4_only(original_getaddrinfo)
    events: list[CalendarEvent] = []
    errors: list[str] = []
    try:
        async with await aio.get_async_davclient(
            url="https://caldav.icloud.com/",
            username=settings.apple_id,
            password=settings.apple_password,
        ) as client:
            principal = await client.principal()
            calendars = await principal.get_calendars()
            for calendar in calendars:
                name = await _wait(calendar.get_display_name())
                calendar_name = name or "Apple"
                try:
                    found = await _wait(
                        calendar.search(
                            event=True,
                            start=start,
                            end=end,
                            expand=True,
                        )
                    )
                except Exception as exc:
                    errors.append(f"Apple / {calendar_name}: {exc}")
                    continue
                for raw in found or []:
                    parsed = await _parse_apple_event(
                        raw,
                        calendar_name=calendar_name,
                        calendar_id=str(calendar.url),
                        timezone=settings.timezone,
                    )
                    if parsed is not None:
                        events.append(parsed)
    finally:
        socket.getaddrinfo = original_getaddrinfo

    events.sort(key=lambda item: item.start_time)
    return CalendarSnapshot(events=events, errors=errors)


async def _parse_apple_event(raw, *, calendar_name: str, calendar_id: str, timezone):
    if not raw.is_loaded():
        await _wait(raw.load())
    component = raw.get_icalendar_component()
    if component is None:
        return None
    return event_from_apple(
        component,
        calendar_name=calendar_name,
        calendar_id=calendar_id,
        event_url=str(getattr(raw, "url", "") or ""),
        timezone=timezone,
    )


def _ipv4_only(original):
    def _resolve(host, port, family=0, type=0, proto=0, flags=0):
        return original(host, port, socket.AF_INET, type, proto, flags)

    return _resolve


async def _wait(value):
    if inspect.isawaitable(value):
        return await value
    return value
