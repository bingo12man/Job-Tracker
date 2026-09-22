from sqlalchemy.orm import Session

from . import models
from .collectors.greenhouse import fetch_greenhouse_jobs
from .experience_parser import parse_experience
from .filters import detect_role, job_matches
from .collectors.lever import fetch_lever_jobs
from .collectors.ashby import fetch_ashby_jobs
from .alerts import send_telegram_alert
from .collectors.smartrecruiters import (
    fetch_smartrecruiters_jobs,
)
from .collectors.workday import (
    fetch_workday_jobs,
)
async def scan_greenhouse_company(
    db: Session,
    company_name: str,
    board_token: str,
    send_alerts: bool = True,
):
    jobs = await fetch_greenhouse_jobs(
        board_token
    )

    new_jobs = []
    matched_jobs = []

    for job in jobs:

        # -------------------------
        # Check duplicate
        # -------------------------
        existing_job = (
            db.query(models.Job)
            .filter(
                models.Job.career_url
                == job["career_url"]
            )
            .first()
        )

        if existing_job:
            continue

        # -------------------------
        # Parse experience
        # -------------------------
        (
            experience_min,
            experience_max,
            experience_not_specified,
        ) = parse_experience(
            job["description"] or "",
            job["title"] or "",
        )

        # -------------------------
        # Detect role
        # -------------------------
        role_category = detect_role(
            job["title"]
        )

        # -------------------------
        # Check match
        # -------------------------
        is_match = job_matches(
            title=job["title"],
            location=job["location"],
            min_experience=experience_min,
            max_experience=experience_max,
        )

        # -------------------------
        # Save job
        # -------------------------
        db_job = models.Job(
            company=company_name,
            external_job_id=job[
                "external_job_id"
            ],
            title=job["title"],
            location=job["location"],
            description=job["description"],
            career_url=job["career_url"],
            source="greenhouse",
            role_category=role_category,
            experience_min=experience_min,
            experience_max=experience_max,
            experience_not_specified=(
                experience_not_specified
            ),
            is_remote=(
                "remote"
                in (
                    job["location"] or ""
                ).lower()
            ),
            is_match=is_match,
        )

        db.add(db_job)

        new_jobs.append(db_job)

        if is_match:
            matched_jobs.append(db_job)

            if send_alerts:
                await send_telegram_alert(
                    db_job
                )

    db.commit()

    return {
        "total_new": len(new_jobs),
        "total_matches": len(matched_jobs),
        "matches": matched_jobs,
    }

async def scan_lever_company(
    db: Session,
    company_name: str,
    company_token: str,
    send_alerts: bool = True,
):
    jobs = await fetch_lever_jobs(
        company_token
    )

    new_jobs = []
    matched_jobs = []

    for job in jobs:

        existing_job = (
            db.query(models.Job)
            .filter(
                models.Job.career_url
                == job["career_url"]
            )
            .first()
        )

        if existing_job:
            continue

        (
            experience_min,
            experience_max,
            experience_not_specified,
        ) = parse_experience(
            job["description"] or "",
            job["title"] or "",
        )

        role_category = detect_role(
            job["title"]
        )

        is_match = job_matches(
            title=job["title"],
            location=job["location"],
            min_experience=experience_min,
            max_experience=experience_max,
        )

        db_job = models.Job(
            company=company_name,
            external_job_id=job[
                "external_job_id"
            ],
            title=job["title"],
            location=job["location"],
            description=job["description"],
            career_url=job["career_url"],
            source="lever",
            role_category=role_category,
            experience_min=experience_min,
            experience_max=experience_max,
            experience_not_specified=(
                experience_not_specified
            ),
            is_remote=(
                "remote"
                in (
                    job["location"] or ""
                ).lower()
            ),
            is_match=is_match,
        )

        db.add(db_job)

        new_jobs.append(db_job)

        if is_match:
            matched_jobs.append(db_job)

            if send_alerts:
                await send_telegram_alert(
                    db_job
                )

    db.commit()

    return {
        "total_new": len(new_jobs),
        "total_matches": len(matched_jobs),
        "matches": matched_jobs,
    }

async def scan_ashby_company(
    db: Session,
    company_name: str,
    board_token: str,
    send_alerts: bool = True,
):
    jobs = await fetch_ashby_jobs(
        board_token
    )

    new_jobs = []
    matched_jobs = []

    for job in jobs:

        existing_job = (
            db.query(models.Job)
            .filter(
                models.Job.career_url
                == job["career_url"]
            )
            .first()
        )

        if existing_job:
            continue

        (
            experience_min,
            experience_max,
            experience_not_specified,
        ) = parse_experience(
            job["description"] or "",
            job["title"] or "",
        )

        role_category = detect_role(
            job["title"]
        )

        is_match = job_matches(
            title=job["title"],
            location=job["location"],
            min_experience=experience_min,
            max_experience=experience_max,
        )

        db_job = models.Job(
            company=company_name,
            external_job_id=job[
                "external_job_id"
            ],
            title=job["title"],
            location=job["location"],
            description=job["description"],
            career_url=job["career_url"],
            source="ashby",
            role_category=role_category,
            experience_min=experience_min,
            experience_max=experience_max,
            experience_not_specified=(
                experience_not_specified
            ),
            is_remote=(
                "remote"
                in (
                    job["location"] or ""
                ).lower()
            ),
            is_match=is_match,
        )

        db.add(db_job)

        new_jobs.append(db_job)

        if is_match:
            matched_jobs.append(db_job)

            if send_alerts:
                await send_telegram_alert(
                    db_job
                )

    db.commit()

    return {
        "total_new": len(new_jobs),
        "total_matches": len(matched_jobs),
        "matches": matched_jobs,
    }

async def scan_smartrecruiters_company(
    db: Session,
    company_name: str,
    company_identifier: str,
    send_alerts: bool = True,
):
    jobs = await fetch_smartrecruiters_jobs(
        company_identifier
    )

    new_jobs = []
    matched_jobs = []

    for job in jobs:

        existing_job = (
            db.query(models.Job)
            .filter(
                models.Job.career_url
                == job["career_url"]
            )
            .first()
        )

        if existing_job:
            continue

        (
            experience_min,
            experience_max,
            experience_not_specified,
        ) = parse_experience(
            job["description"] or "",
            job["title"] or "",
        )

        role_category = detect_role(
            job["title"]
        )

        is_match = job_matches(
            title=job["title"],
            location=job["location"],
            min_experience=experience_min,
            max_experience=experience_max,
        )

        db_job = models.Job(
            company=company_name,

            external_job_id=job[
                "external_job_id"
            ],

            title=job["title"],
            location=job["location"],
            description=job["description"],
            career_url=job["career_url"],

            source="smartrecruiters",

            role_category=role_category,

            experience_min=
                experience_min,

            experience_max=
                experience_max,

            experience_not_specified=
                experience_not_specified,

            is_remote=(
                "remote"
                in (
                    job["location"]
                    or ""
                ).lower()
            ),

            is_match=is_match,
        )

        db.add(db_job)

        new_jobs.append(
            db_job
        )

        if is_match:
            matched_jobs.append(
                db_job
            )

            if send_alerts:
                await send_telegram_alert(
                    db_job
                )

    db.commit()

    return {
        "total_new": len(new_jobs),
        "total_matches": len(
            matched_jobs
        ),
        "matches": matched_jobs,
    }

async def scan_workday_company(
    db: Session,
    company_name: str,
    career_url: str,
    send_alerts: bool = True,
):
    jobs = await fetch_workday_jobs(
        career_url
    )

    new_jobs = []
    matched_jobs = []

    for job in jobs:

        existing_job = (
            db.query(models.Job)
            .filter(
                models.Job.career_url
                == job["career_url"]
            )
            .first()
        )

        if existing_job:
            continue

        (
            experience_min,
            experience_max,
            experience_not_specified,
        ) = parse_experience(
            job["description"] or "",
            job["title"] or "",
        )

        role_category = detect_role(
            job["title"]
        )

        is_match = job_matches(
            title=job["title"],
            location=job["location"],
            min_experience=experience_min,
            max_experience=experience_max,
        )

        db_job = models.Job(
            company=company_name,
            external_job_id=job[
                "external_job_id"
            ],
            title=job["title"],
            location=job["location"],
            description=job[
                "description"
            ],
            career_url=job[
                "career_url"
            ],
            source="workday",
            role_category=role_category,
            experience_min=
                experience_min,
            experience_max=
                experience_max,
            experience_not_specified=
                experience_not_specified,
            is_remote=(
                "remote"
                in (
                    job["location"]
                    or ""
                ).lower()
            ),
            is_match=is_match,
        )

        db.add(db_job)

        new_jobs.append(
            db_job
        )

        if is_match:
            matched_jobs.append(
                db_job
            )

            if send_alerts:
                await send_telegram_alert(
                    db_job
                )

    db.commit()

    return {
        "total_new": len(new_jobs),
        "total_matches": len(
            matched_jobs
        ),
        "matches": matched_jobs,
    }