import httpx


SMARTRECRUITERS_API = (
    "https://api.smartrecruiters.com/v1/companies/"
    "{company_identifier}/postings"
)


async def fetch_smartrecruiters_jobs(
    company_identifier: str,
):
    url = SMARTRECRUITERS_API.format(
        company_identifier=company_identifier
    )

    async with httpx.AsyncClient(
        timeout=20.0
    ) as client:
        response = await client.get(url)

    if response.status_code == 404:
        raise ValueError(
            f"SmartRecruiters company "
            f"'{company_identifier}' was not found."
        )

    if response.status_code != 200:
        raise Exception(
            f"SmartRecruiters returned "
            f"status {response.status_code}"
        )

    data = response.json()

    jobs = []

    for job in data.get("content", []):

        location_data = job.get(
            "location",
            {},
        )

        location_parts = [
            location_data.get("city"),
            location_data.get("region"),
            location_data.get("country"),
        ]

        location = ", ".join(
            part
            for part in location_parts
            if part
        )

        external_job_id = str(
            job.get("id")
        )

        # Fetch full description
        details_url = (
            f"https://api.smartrecruiters.com/"
            f"v1/companies/"
            f"{company_identifier}/postings/"
            f"{external_job_id}"
        )

        async with httpx.AsyncClient(
            timeout=20.0
        ) as client:
            details_response = await client.get(
                details_url
            )

        description = ""

        career_url = None

        if details_response.status_code == 200:
            details = details_response.json()

            job_ad = details.get(
                "jobAd",
                {}
            )

            sections = job_ad.get(
                "sections",
                {}
            )

            description_parts = []

            for section in sections.values():

                if isinstance(section, dict):

                    text = section.get(
                        "text"
                    )

                    if text:
                        description_parts.append(
                            text
                        )

            description = "\n".join(
                description_parts
            )

            career_url = details.get(
                "postingUrl"
            )

        if not career_url:
            career_url = (
                f"https://jobs.smartrecruiters.com/"
                f"{company_identifier}/"
                f"{external_job_id}"
            )

        jobs.append({
            "external_job_id":
                external_job_id,

            "title":
                job.get("name"),

            "location":
                location,

            "description":
                description,

            "career_url":
                career_url,

            "posted_at":
                job.get("releasedDate"),

            "source":
                "smartrecruiters",
        })

    return jobs