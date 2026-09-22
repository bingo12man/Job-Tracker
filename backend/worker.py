import asyncio

from app.scheduler import start_scheduler


async def main():
    start_scheduler()

    print(
        "Job Radar worker running."
    )

    # Keep worker alive forever
    while True:
        await asyncio.sleep(3600)


if __name__ == "__main__":
    asyncio.run(main())