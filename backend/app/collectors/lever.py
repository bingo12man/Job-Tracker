import httpx


LEVER_API = "https://api.lever.co/v0/postings/{company_token}?mode=json"


async def fetch_lever_jobs(company_token: str):
    url = LEVER_API.format(
        company_token=company_token
    )

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:
        response = await client.get(url)

    if response.status_code == 404:
        raise ValueError(
            f"Lever company '{company_token}' was not found."
        )

    if response.status_code != 200:
        raise Exception(
            f"Lever returned status {response.status_code}"
        )

    data = response.json()

    jobs = []

    for job in data:

        categories = job.get("categories", {})

        location = categories.get("location")

        description_parts = [
            job.get("descriptionPlain", ""),
        ]

        for section in job.get("lists", []):
            description_parts.append(
                section.get("text", "")
            )

            for item in section.get("content", "").split("\n"):
                description_parts.append(item)

        description = "\n".join(
            part for part in description_parts if part
        )

        jobs.append({
            "external_job_id": job.get("id"),
            "title": job.get("text"),
            "location": location,
            "description": description,
            "career_url": job.get("hostedUrl"),
            "posted_at": None,
            "source": "lever",
        })

    return jobs