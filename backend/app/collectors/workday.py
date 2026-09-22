import re
from urllib.parse import urlparse

import httpx


WORKDAY_HOST_PATTERN = re.compile(
    r"^([a-zA-Z0-9-]+)\.(wd\d+)\.myworkdayjobs\.com$"
)


def parse_workday_url(career_url: str):
    """
    Example:
    https://nvidia.wd5.myworkdayjobs.com/en-US/NVIDIAExternalCareerSite

    Returns:
    {
        "hostname": "nvidia.wd5.myworkdayjobs.com",
        "tenant": "nvidia",
        "site": "NVIDIAExternalCareerSite"
    }
    """

    parsed = urlparse(career_url)

    hostname = parsed.hostname

    if not hostname:
        raise ValueError(
            "Invalid Workday career URL"
        )

    match = WORKDAY_HOST_PATTERN.match(
        hostname
    )

    if not match:
        raise ValueError(
            "URL does not look like a valid "
            "Workday myworkdayjobs.com URL"
        )

    tenant = match.group(1)

    path_parts = [
        part
        for part in parsed.path.split("/")
        if part
    ]

    # Example:
    # /en-US/NVIDIAExternalCareerSite
    #
    # Remove locale if present.
    if (
        path_parts
        and re.match(
            r"^[a-z]{2}-[A-Z]{2}$",
            path_parts[0],
        )
    ):
        path_parts.pop(0)

    if not path_parts:
        raise ValueError(
            "Could not determine Workday site name"
        )

    site = path_parts[0]

    return {
        "hostname": hostname,
        "tenant": tenant,
        "site": site,
    }


def extract_location_from_job_info(
    job_info: dict,
    fallback_location: str | None,
):
    """
    Workday sometimes returns:
        "4 Locations"

    This tries to replace that with the actual
    locations from the detail API.
    """

    locations = []

    # ----------------------------------
    # PRIMARY LOCATION
    # ----------------------------------
    primary_location = job_info.get(
        "location"
    )

    if isinstance(primary_location, str):
        if primary_location.strip():
            locations.append(
                primary_location.strip()
            )

    elif isinstance(primary_location, dict):
        primary_name = (
            primary_location.get("name")
            or primary_location.get("location")
            or primary_location.get(
                "descriptor"
            )
        )

        if primary_name:
            locations.append(
                str(primary_name).strip()
            )

    # ----------------------------------
    # ADDITIONAL LOCATIONS
    # ----------------------------------
    additional_locations = (
        job_info.get(
            "additionalLocations",
            []
        )
    )

    if isinstance(
        additional_locations,
        list
    ):
        for location in additional_locations:

            if isinstance(location, str):
                location = location.strip()

                if location:
                    locations.append(
                        location
                    )

            elif isinstance(location, dict):

                location_name = (
                    location.get("name")
                    or location.get("location")
                    or location.get(
                        "descriptor"
                    )
                )

                if location_name:
                    locations.append(
                        str(
                            location_name
                        ).strip()
                    )

    # ----------------------------------
    # REMOVE DUPLICATES
    # ----------------------------------
    locations = list(
        dict.fromkeys(
            location
            for location in locations
            if location
        )
    )

    if locations:
        return ", ".join(locations)

    return fallback_location


async def fetch_workday_jobs(
    career_url: str,
):
    info = parse_workday_url(
        career_url
    )

    hostname = info["hostname"]
    tenant = info["tenant"]
    site = info["site"]

    # ----------------------------------
    # WORKDAY LIST API
    # ----------------------------------
    jobs_api_url = (
        f"https://{hostname}"
        f"/wday/cxs/"
        f"{tenant}/"
        f"{site}/jobs"
    )

    jobs = []

    offset = 0
    limit = 20

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
        headers={
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": (
                "Mozilla/5.0 "
                "(Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 "
                "(KHTML, like Gecko) "
                "Chrome/120.0 Safari/537.36"
            ),
            "Referer": career_url,
        },
    ) as client:

        while True:

            payload = {
                "appliedFacets": {},
                "limit": limit,
                "offset": offset,
                "searchText": "",
            }

            response = await client.post(
                jobs_api_url,
                json=payload,
            )

            if response.status_code == 404:
                raise ValueError(
                    f"Workday board not found: "
                    f"{career_url}"
                )

            if response.status_code != 200:
                raise Exception(
                    f"Workday returned "
                    f"status "
                    f"{response.status_code}"
                )

            data = response.json()

            postings = data.get(
                "jobPostings",
                [],
            )

            if not postings:
                break

            # ----------------------------------
            # PROCESS EACH JOB
            # ----------------------------------
            for job in postings:

                external_path = (
                    job.get(
                        "externalPath"
                    )
                    or ""
                )

                # If Workday didn't provide a path,
                # skip the job because we cannot
                # uniquely identify/fetch it.
                if not external_path:
                    continue

                # ----------------------------------
                # PUBLIC JOB URL
                # ----------------------------------
                job_url = (
                    f"https://{hostname}"
                    f"/{site}"
                    f"{external_path}"
                )

                # ----------------------------------
                # DETAIL API URL
                # ----------------------------------
                detail_api_url = (
                    f"https://{hostname}"
                    f"/wday/cxs/"
                    f"{tenant}/"
                    f"{site}"
                    f"{external_path}"
                )

                description = ""

                final_location = (
                    job.get(
                        "locationsText"
                    )
                )

                # ----------------------------------
                # FETCH FULL JOB DETAILS
                # ----------------------------------
                try:
                    detail_response = (
                        await client.get(
                            detail_api_url
                        )
                    )

                    if (
                        detail_response.status_code
                        == 200
                    ):
                        detail_data = (
                            detail_response.json()
                        )

                        job_info = (
                            detail_data.get(
                                "jobPostingInfo",
                                {}
                            )
                        )

                        # FULL DESCRIPTION
                        description = (
                            job_info.get(
                                "jobDescription",
                                ""
                            )
                            or ""
                        )

                        # ACTUAL LOCATION(S)
                        final_location = (
                            extract_location_from_job_info(
                                job_info,
                                final_location,
                            )
                        )

                except Exception as e:
                    print(
                        f"Could not fetch Workday "
                        f"job details for "
                        f"{external_path}: {e}"
                    )

                # ----------------------------------
                # EXTERNAL JOB ID
                # ----------------------------------
                external_job_id = (
                    external_path
                    .rstrip("/")
                    .split("/")[-1]
                )

                jobs.append({
                    "external_job_id":
                        external_job_id,

                    "title":
                        job.get("title"),

                    "location":
                        final_location,

                    "description":
                        description,

                    "career_url":
                        job_url,

                    "posted_at":
                        job.get(
                            "postedOn"
                        ),

                    "source":
                        "workday",
                })

            # ----------------------------------
            # PAGINATION
            # ----------------------------------
            offset += limit

            total = data.get(
                "total",
                0,
            )

            if offset >= total:
                break

    return jobs