import os

import httpx
from dotenv import load_dotenv


load_dotenv()


TELEGRAM_BOT_TOKEN = os.getenv(
    "TELEGRAM_BOT_TOKEN"
)

TELEGRAM_CHAT_ID = os.getenv(
    "TELEGRAM_CHAT_ID"
)


async def send_telegram_alert(job):
    if not TELEGRAM_BOT_TOKEN:
        print("Telegram token missing")
        return False

    if not TELEGRAM_CHAT_ID:
        print("Telegram chat ID missing")
        return False

    if (
        job.experience_min is None
        and job.experience_max is None
    ):
        experience_text = "Not specified"

    elif (
        job.experience_min is not None
        and job.experience_max is None
    ):
        experience_text = f"{job.experience_min}+ years"

    elif (
        job.experience_min is None
        and job.experience_max is not None
    ):
        experience_text = f"Up to {job.experience_max} years"

    else:
        experience_text = (
            f"{job.experience_min} - "
            f"{job.experience_max} years"
        )

    message = f"""
🚨 NEW MATCHING JOB

Company: {job.company}

Role:
{job.title}

Location:
{job.location or "Not specified"}

Experience:
{experience_text}

Apply:
{job.career_url}
"""

    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:

        response = await client.post(
            url,
            json={
                "chat_id": TELEGRAM_CHAT_ID,
                "text": message,
            },
        )

    return response.status_code == 200