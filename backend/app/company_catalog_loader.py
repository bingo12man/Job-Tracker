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
    seen = set()

    async with httpx.AsyncClient(
        timeout=30.0,
        follow_redirects=True,
    ) as client:

        # ----------------------------------
        # 1. INDIA-FOCUSED CATALOG
        # ----------------------------------

        response = await client.get(
            INDIA_SOURCE
        )

        response.raise_for_status()

        data = yaml.safe_load(
            response.text
        )

        for ats_type in [
            "greenhouse",
            "lever",
            "ashby",
        ]:

            rows = data.get(
                ats_type,
                []
            )

            for row in rows:

                name = row.get("name")
                token = row.get("slug")

                if not name or not token:
                    continue

                key = (
                    ats_type,
                    token.lower(),
                )

                if key in seen:
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

                else:
                    url = (
                        "https://jobs.ashbyhq.com/"
                        f"{token}"
                    )

                companies.append(
                    make_company(
                        name,
                        ats_type,
                        token,
                        url,
                    )
                )

                seen.add(key)

        # ----------------------------------
        # 2. GLOBAL TECH COMPANY CATALOG
        # ----------------------------------

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
            "Greenhouse": "greenhouse",
            "Lever": "lever",
            "Ashby": "ashby",
            "SmartRecruiters":
                "smartrecruiters",
        }

        for row in reader:

            if len(companies) >= limit:
                break

            if (
                row.get("verified", "")
                .lower()
                != "true"
            ):
                continue

            source_ats = row.get(
                "ats_system",
                ""
            )

            ats_type = ats_mapping.get(
                source_ats
            )

            if not ats_type:
                continue

            name = row.get("name")
            token = row.get("slug")

            if not name or not token:
                continue

            key = (
                ats_type,
                token.lower(),
            )

            if key in seen:
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

                url = (
                    "https://careers."
                    "smartrecruiters.com/"
                    f"{token}"
                )

            companies.append(
                make_company(
                    name,
                    ats_type,
                    token,
                    url,
                )
            )

            seen.add(key)

    return companies[:limit]
