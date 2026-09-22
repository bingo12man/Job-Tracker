import csv
import io
import httpx
import yaml


INDIA_SOURCE = (
    "https://raw.githubusercontent.com/"
    "AnojSKunte/career-ops-india/main/portals/india.yml"
)

GLOBAL_SOURCE = (
    "https://raw.githubusercontent.com/"
    "Kayvan-Zahiri/state-of-ats-2026/main/data/companies.csv"
)


def make_company(
    name,
    ats_type,
    token,
    career_url,
):
    return {
        "name": name.strip(),
        "ats_type": ats_type,
        "board_token": token.strip(),
        "career_url": career_url.strip(),
        "enabled": True,
    }


async def load_company_catalog(
    limit: int = 600,
):
    companies = []

    # Deduplicate by company name
    # because companies.name is UNIQUE in PostgreSQL
    seen_names = set()

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
    ) as client:

        # ==================================
        # 1. INDIA-FOCUSED CATALOG
        # ==================================

        response = await client.get(
            INDIA_SOURCE
        )

        response.raise_for_status()

        data = yaml.safe_load(
            response.text
        ) or {}

        for ats_type in [
            "greenhouse",
            "lever",
            "ashby",
        ]:

            rows = data.get(
                ats_type,
                []
            ) or []

            for row in rows:

                if len(companies) >= limit:
                    break

                name = row.get("name")
                token = row.get("slug")

                if not name or not token:
                    continue

                name = name.strip()
                token = token.strip()

                normalized_name = (
                    name.lower()
                )

                # Prevent same company name
                # appearing under multiple ATS
                if normalized_name in seen_names:
                    continue

                if ats_type == "greenhouse":

                    url = (
                        "https://job-boards."
                        "greenhouse.io/"
                        f"{token}"
                    )

                elif ats_type == "lever":

                    url = (
                        "https://jobs.lever.co/"
                        f"{token}"
                    )

                elif ats_type == "ashby":

                    url = (
                        "https://jobs."
                        "ashbyhq.com/"
                        f"{token}"
                    )

                else:
                    continue

                companies.append(
                    make_company(
                        name=name,
                        ats_type=ats_type,
                        token=token,
                        career_url=url,
                    )
                )

                seen_names.add(
                    normalized_name
                )

            if len(companies) >= limit:
                break

        # ==================================
        # 2. GLOBAL TECH COMPANY CATALOG
        # ==================================

        if len(companies) < limit:

            response = await client.get(
                GLOBAL_SOURCE
            )

            response.raise_for_status()

            reader = csv.DictReader(
                io.StringIO(
                    response.text
                )
            )

            ats_mapping = {
                "Greenhouse":
                    "greenhouse",

                "Lever":
                    "lever",

                "Ashby":
                    "ashby",

                "SmartRecruiters":
                    "smartrecruiters",
            }

            for row in reader:

                if len(companies) >= limit:
                    break

                verified = (
                    row.get(
                        "verified",
                        ""
                    )
                    .strip()
                    .lower()
                )

                if verified != "true":
                    continue

                source_ats = (
                    row.get(
                        "ats_system",
                        ""
                    )
                    .strip()
                )

                ats_type = (
                    ats_mapping.get(
                        source_ats
                    )
                )

                if not ats_type:
                    continue

                name = row.get("name")
                token = row.get("slug")

                if not name or not token:
                    continue

                name = name.strip()
                token = token.strip()

                normalized_name = (
                    name.lower()
                )

                # IMPORTANT:
                # Deduplicate by company name,
                # not by ATS/token
                if normalized_name in seen_names:
                    continue

                if ats_type == "greenhouse":

                    url = (
                        "https://job-boards."
                        "greenhouse.io/"
                        f"{token}"
                    )

                elif ats_type == "lever":

                    url = (
                        "https://jobs.lever.co/"
                        f"{token}"
                    )

                elif ats_type == "ashby":

                    url = (
                        "https://jobs."
                        "ashbyhq.com/"
                        f"{token}"
                    )

                elif ats_type == "smartrecruiters":

                    url = (
                        "https://careers."
                        "smartrecruiters.com/"
                        f"{token}"
                    )

                else:
                    continue

                companies.append(
                    make_company(
                        name=name,
                        ats_type=ats_type,
                        token=token,
                        career_url=url,
                    )
                )

                seen_names.add(
                    normalized_name
                )

    return companies[:limit]
