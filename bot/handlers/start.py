from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer(
        "Привет. Я читаю Google Calendar и iCloud и присылаю события одним списком.\n"
        "Команда /upcoming — события на ближайшие 7 дней."
    )
