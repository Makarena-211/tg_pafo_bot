from datetime import datetime

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from calendars.models import CalendarEvent, CalendarSnapshot
from calendars.normalize import event_from_google
from config import Settings

SCOPES = ["https://www.googleapis.com/auth/calendar"]


def fetch_google_events(
    settings: Settings,
    start: datetime,
    end: datetime,
) -> CalendarSnapshot:
    """События Google Calendar за интервал [start, end) в общем формате."""
    service = _calendar_service(settings)
    events: list[CalendarEvent] = []
    errors: list[str] = []

    for calendar in _list_calendars(service):
        calendar_id = calendar["id"]
        calendar_name = calendar.get("summary") or calendar_id
        try:
            for item in _list_events(service, calendar_id, start, end):
                parsed = event_from_google(
                    item,
                    calendar_name=calendar_name,
                    calendar_id=calendar_id,
                    timezone=settings.timezone,
                )
                if parsed is not None:
                    events.append(parsed)
        except Exception as exc:
            errors.append(f"Google / {calendar_name}: {exc}")

    events.sort(key=lambda item: item.start_time)
    return CalendarSnapshot(events=events, errors=errors)


def _calendar_service(settings: Settings):
    creds = Credentials.from_authorized_user_file(settings.google_creds_path, SCOPES)
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(settings.google_creds_path, "w", encoding="utf-8") as token_file:
                token_file.write(creds.to_json())
        else:
            raise RuntimeError("Google-токен недействителен, нужна повторная авторизация")
    return build("calendar", "v3", credentials=creds)


def _list_calendars(service) -> list[dict]:
    calendars: list[dict] = []
    page_token = None
    while True:
        response = service.calendarList().list(pageToken=page_token).execute()
        for item in response.get("items", []):
            if item.get("deleted"):
                continue
            calendars.append(item)
        page_token = response.get("nextPageToken")
        if not page_token:
            return calendars


def _list_events(service, calendar_id: str, start: datetime, end: datetime) -> list[dict]:
    events: list[dict] = []
    page_token = None
    while True:
        response = (
            service.events()
            .list(
                calendarId=calendar_id,
                timeMin=start.isoformat(),
                timeMax=end.isoformat(),
                singleEvents=True,
                orderBy="startTime",
                pageToken=page_token,
            )
            .execute()
        )
        events.extend(response.get("items", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            return events
