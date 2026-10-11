import asyncio
from datetime import datetime, timedelta

from calendars.apple import fetch_apple_events
from config import load_settings


async def main():
    settings = load_settings()
    start = datetime.now(settings.timezone)
    end = start + timedelta(days=31)
    snapshot = await fetch_apple_events(settings, start, end)
    for event in snapshot.events:
        print(event.model_dump())
    for error in snapshot.errors:
        print(error)


if __name__ == "__main__":
    asyncio.run(main())
