import httpx


ASHBY_API = "https://api.ashbyhq.com/posting-api/job-board/{board_token}"


async def fetch_ashby_jobs(board_token: str):
    url = ASHBY_API.format(
        board_token=board_token
    )

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:
        response = await client.get(url)

    if response.status_code == 404:
        raise ValueError(
            f"Ashby board '{board_token}' was not found."
        )

    if response.status_code != 200:
        raise Exception(
            f"Ashby returned status {response.status_code}"
        )

    data = response.json()

    jobs = []

    for job in data.get("jobs", []):

        location = job.get("location")

        description = (
            job.get("descriptionPlain")
            or job.get("descriptionHtml")
            or ""
        )

        jobs.append({
            "external_job_id": job.get("id"),
            "title": job.get("title"),
            "location": location,
            "description": description,
            "career_url": job.get("jobUrl"),
            "posted_at": job.get("publishedAt"),
            "source": "ashby",
        })

    return jobs