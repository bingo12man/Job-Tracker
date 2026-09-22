import httpx


GREENHOUSE_API = (
    "https://boards-api.greenhouse.io/v1/boards/"
    "{board_token}/jobs"
)


async def fetch_greenhouse_jobs(board_token: str):

    url = GREENHOUSE_API.format(
        board_token=board_token
    )

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:

        try:
            response = await client.get(
                url,
                params={
                    "content": "true"
                }
            )

        except httpx.RequestError as e:
            raise Exception(
                f"Could not connect to Greenhouse: {e}"
            )

    if response.status_code == 404:
        raise ValueError(
            f"Greenhouse board '{board_token}' was not found."
        )

    if response.status_code != 200:
        raise Exception(
            f"Greenhouse returned "
            f"status {response.status_code}"
        )

    data = response.json()

    jobs = []

    for job in data.get("jobs", []):

        jobs.append(
            {
                "external_job_id": str(
                    job.get("id")
                ),

                "title": job.get(
                    "title"
                ),

                "location": (
                    job.get("location", {})
                    .get("name")
                ),

                "description": job.get(
                    "content"
                ),

                "career_url": job.get(
                    "absolute_url"
                ),

                "posted_at": job.get(
                    "updated_at"
                ),

                "source": "greenhouse",
            }
        )

    return jobs