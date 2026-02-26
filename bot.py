import asyncio
import re
import os
from datetime import datetime, timedelta, time

from aiogram import Bot, Dispatcher
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

TOKEN = os.getenv("8742536061:AAFEe4d-CpRje_p7gOzwYlLdSN47F-AdVGw")
GROUP_ID = -4770091083  # ID группы

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()

active_requests = {}

WORK_START = time(9, 0)
WORK_END = time(18, 0)
SLA_MINUTES = 60


def is_request(text: str):
    inn_pattern = r"\b\d{9}\b"
    phone_pattern = r"\b\d{9,12}\b"
    return bool(re.search(inn_pattern, text) and re.search(phone_pattern, text))


def calculate_deadline(now: datetime):

    if now.weekday() == 6:
        next_day = now + timedelta(days=1)
        return datetime.combine(next_day.date(), WORK_START) + timedelta(minutes=SLA_MINUTES)

    if now.time() >= WORK_END:
        next_day = now + timedelta(days=1)

        if next_day.weekday() == 6:
            next_day += timedelta(days=1)

        return datetime.combine(next_day.date(), WORK_START) + timedelta(minutes=SLA_MINUTES)

    if now.time() < WORK_START:
        return datetime.combine(now.date(), WORK_START) + timedelta(minutes=SLA_MINUTES)

    return now + timedelta(minutes=SLA_MINUTES)


async def monitor_request(chat_id: int, message_id: int, deadline: datetime):
    seconds = (deadline - datetime.now()).total_seconds()

    if seconds > 0:
        await asyncio.sleep(seconds)

    if message_id in active_requests:
        await bot.send_message(
            chat_id,
            f"⚠️ Заявка без ответа более {SLA_MINUTES} минут"
        )


@dp.message()
async def handle_message(message: Message):

    if message.text and is_request(message.text):
        now = datetime.now()
        deadline = calculate_deadline(now)

        active_requests[message.message_id] = deadline

        asyncio.create_task(
            monitor_request(message.chat.id, message.message_id, deadline)
        )

        if now.time() >= WORK_END or now.weekday() == 6:
            await message.reply(
                "Спасибо за обращение.\n"
                "⏰ Заявки обрабатываются с 09:00 до 18:00."
            )

    if message.reply_to_message:
        original_id = message.reply_to_message.message_id
        if original_id in active_requests:
            del active_requests[original_id]
            await message.reply("✅ Заявка закрыта.")


async def main():
    await dp.start_polling(bot)


if __name__ == "__main__":

    asyncio.run(main())
