from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from calendars.models import CalendarEvent


def event_from_apple(
    component,
    *,
    calendar_name: str,
    calendar_id: str,
    event_url: str,
    timezone: ZoneInfo,
) -> CalendarEvent | None:
    start_prop = component.get("dtstart")
    if start_prop is None:
        return None

    start_raw = start_prop.dt
    all_day = isinstance(start_raw, date) and not isinstance(start_raw, datetime)
    start = _as_aware(start_raw, timezone)
    stop = _apple_stop(component, start, all_day, timezone)
    uid = str(component.get("uid") or event_url or calendar_id)
    return CalendarEvent(
        id=f"{uid}#{start.isoformat()}",
        source="apple",
        calendar_name=calendar_name,
        calendar_id=calendar_id,
        summary=_text(component.get("summary")) or "Без названия",
        start_time=start,
        stop_time=stop,
        all_day=all_day,
    )


def event_from_google(
    item: dict,
    *,
    calendar_name: str,
    calendar_id: str,
    timezone: ZoneInfo,
) -> CalendarEvent | None:
    if item.get("status") == "cancelled":
        return None
    start_payload = item.get("start") or {}
    if "dateTime" not in start_payload and "date" not in start_payload:
        return None

    start, all_day = _google_bound(start_payload, timezone)
    stop_payload = item.get("end") or {}
    if stop_payload:
        stop, _ = _google_bound(stop_payload, timezone)
    elif all_day:
        stop = start + timedelta(days=1)
    else:
        stop = start

    return CalendarEvent(
        id=str(item.get("id") or f"{calendar_id}#{start.isoformat()}"),
        source="google",
        calendar_name=calendar_name,
        calendar_id=calendar_id,
        summary=_text(item.get("summary")) or "Без названия",
        start_time=start,
        stop_time=stop,
        all_day=all_day,
    )


def _apple_stop(component, start: datetime, all_day: bool, timezone: ZoneInfo) -> datetime:
    dtend = component.get("dtend")
    if dtend is not None:
        return _as_aware(dtend.dt, timezone)
    try:
        duration = component.duration
    except Exception:
        duration = None
    if duration:
        return start + duration
    if all_day:
        return start + timedelta(days=1)
    return start


def _google_bound(payload: dict, timezone: ZoneInfo) -> tuple[datetime, bool]:
    if "dateTime" in payload:
        raw = datetime.fromisoformat(str(payload["dateTime"]).replace("Z", "+00:00"))
        return _as_aware(raw, timezone), False
    day = date.fromisoformat(str(payload["date"]))
    return datetime.combine(day, time.min, tzinfo=timezone), True


def _as_aware(value: date | datetime, timezone: ZoneInfo) -> datetime:
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone)
        return value.astimezone(timezone)
    return datetime.combine(value, time.min, tzinfo=timezone)


def _text(value) -> str:
    if value is None:
        return ""
    return str(value).strip()
