from datetime import datetime, timedelta

from calendars.google import fetch_google_events
from config import load_settings


def main():
    settings = load_settings()
    start = datetime.now(settings.timezone)
    end = start + timedelta(days=31)
    snapshot = fetch_google_events(settings, start, end)
    for event in snapshot.events:
        print(event.model_dump())
    for error in snapshot.errors:
        print(error)


if __name__ == "__main__":
    main()
