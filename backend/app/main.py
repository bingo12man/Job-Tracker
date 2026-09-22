from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime
from . import models, schemas
from .database import engine, get_db
from .filters import detect_role, job_matches
from .experience_parser import parse_experience
from .scanner import (
    scan_greenhouse_company,
    scan_lever_company,
    scan_ashby_company,
    scan_smartrecruiters_company,
    scan_workday_company,
)
from fastapi import HTTPException
from .filters import (
    detect_role,
    job_matches,
    evaluate_job,
)
from .experience_parser import parse_experience
from contextlib import asynccontextmanager
from .alerts import send_telegram_alert
from datetime import datetime
from .seed_companies import SEED_COMPANIES
models.Base.metadata.create_all(bind=engine)
from .alerts import send_telegram_alert
from fastapi.middleware.cors import CORSMiddleware
import time
models.Base.metadata.create_all(bind=engine)
import os

from .company_catalog_loader import (
    load_company_catalog,
)


FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Job Radar API",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "message": "Job Radar API is running"
    }


@app.post(
    "/jobs",
    response_model=schemas.JobResponse,
)
def create_job(
    job: schemas.JobCreate,
    db: Session = Depends(get_db),
):
    experience_min = job.experience_min
    experience_max = job.experience_max

    if experience_min is None and experience_max is None:
        (
            experience_min,
            experience_max,
            experience_not_specified,
        ) = parse_experience(job.description or "")
    else:
        experience_not_specified = False
    role_category = detect_role(job.title)

    is_match = job_matches(
    title=job.title,
    location=job.location,
    min_experience=experience_min,
    max_experience=experience_max,
)

    db_job = models.Job(
        company=job.company,
        external_job_id=job.external_job_id,
        title=job.title,
        location=job.location,
        description=job.description,
        career_url=job.career_url,
        source=job.source,
        role_category=role_category,
        experience_min=experience_min,
        experience_max=experience_max,
        experience_not_specified=experience_not_specified,
        is_remote=job.is_remote,
        is_match=is_match,
        posted_at=job.posted_at,
    )

    db.add(db_job)
    db.commit()
    db.refresh(db_job)

    return db_job


@app.get(
    "/jobs",
    response_model=list[schemas.JobResponse],
)
def get_jobs(
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Job)
        .order_by(models.Job.first_seen_at.desc())
        .all()
    )


@app.get(
    "/jobs/matches",
    response_model=list[schemas.JobResponse],
)
def get_matching_jobs(
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Job)
        .filter(models.Job.is_match == True)
        .order_by(models.Job.first_seen_at.desc())
        .all()
    )

@app.post("/scan/greenhouse")
async def scan_greenhouse(
    company: str,
    board_token: str,
    db: Session = Depends(get_db),
):

    try:
        result = await scan_greenhouse_company(
            db=db,
            company_name=company,
            board_token=board_token,
        )

    except ValueError as e:
        raise HTTPException(
            status_code=404,
            detail=str(e),
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e),
        )

    return {
        "company": company,
        "source": "greenhouse",
        "new_jobs": result["total_new"],
        "matching_jobs": result["total_matches"],
    }

@app.get("/debug/jobs")
def debug_jobs(
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(models.Job)
        .order_by(models.Job.first_seen_at.desc())
        .limit(100)
        .all()
    )

    results = []

    for job in jobs:

        evaluation = evaluate_job(
            title=job.title,
            location=job.location,
            min_experience=job.experience_min,
            max_experience=job.experience_max,
        )

        results.append({
            "company": job.company,
            "title": job.title,
            "location": job.location,

            "experience_min":
                job.experience_min,

            "experience_max":
                job.experience_max,

            **evaluation,
        })

    return results


@app.post(
    "/companies",
    response_model=schemas.CompanyResponse,
)
def create_company(
    company: schemas.CompanyCreate,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(models.Company)
        .filter(models.Company.name == company.name)
        .first()
    )

    if existing:
        raise HTTPException(
            status_code=400,
            detail="Company already exists",
        )

    db_company = models.Company(
        name=company.name,
        career_url=company.career_url,
        ats_type=company.ats_type.lower(),
        board_token=company.board_token,
        enabled=company.enabled,
    )

    db.add(db_company)
    db.commit()
    db.refresh(db_company)

    return db_company


@app.get(
    "/companies",
    response_model=list[schemas.CompanyResponse],
)
def get_companies(
    db: Session = Depends(get_db),
):
    return (
        db.query(models.Company)
        .order_by(models.Company.name.asc())
        .all()
    )

@app.post("/scan/all")
async def scan_all_companies(
    batch: int = 0,
    batch_size: int = 25,
    db: Session = Depends(get_db),
):
    start_time = time.perf_counter()

    if batch < 0:
        raise HTTPException(
            status_code=400,
            detail="batch must be 0 or greater",
        )

    if batch_size < 1 or batch_size > 50:
        raise HTTPException(
            status_code=400,
            detail="batch_size must be between 1 and 50",
        )

    query = (
        db.query(models.Company)
        .filter(models.Company.enabled == True)
        .order_by(models.Company.id)
    )

    total_companies = query.count()

    companies = (
        query
        .offset(batch * batch_size)
        .limit(batch_size)
        .all()
    )

    total_success = 0
    total_skipped = 0
    total_errors = 0
    total_new_jobs = 0
    total_matching_jobs = 0

    results = []

    for company in companies:

        try:

            # =============================
            # GREENHOUSE
            # =============================

            if company.ats_type == "greenhouse":

                if not company.board_token:
                    raise ValueError(
                        "Missing Greenhouse board token"
                    )

                result = await scan_greenhouse_company(
                    db=db,
                    company_name=company.name,
                    board_token=company.board_token,
                )

            # =============================
            # LEVER
            # =============================

            elif company.ats_type == "lever":

                if not company.board_token:
                    raise ValueError(
                        "Missing Lever company token"
                    )

                result = await scan_lever_company(
                    db=db,
                    company_name=company.name,
                    company_token=company.board_token,
                )

            # =============================
            # ASHBY
            # =============================

            elif company.ats_type == "ashby":

                if not company.board_token:
                    raise ValueError(
                        "Missing Ashby board token"
                    )

                result = await scan_ashby_company(
                    db=db,
                    company_name=company.name,
                    board_token=company.board_token,
                )

            # =============================
            # SMARTRECRUITERS
            # =============================

            elif company.ats_type == "smartrecruiters":

                if not company.board_token:
                    raise ValueError(
                        "Missing SmartRecruiters identifier"
                    )

                result = await scan_smartrecruiters_company(
                    db=db,
                    company_name=company.name,
                    company_identifier=company.board_token,
                )

            # =============================
            # WORKDAY
            # =============================

            elif company.ats_type == "workday":

                if not company.career_url:
                    raise ValueError(
                        "Missing Workday career URL"
                    )

                result = await scan_workday_company(
                    db=db,
                    company_name=company.name,
                    career_url=company.career_url,
                )

            # =============================
            # UNSUPPORTED ATS
            # =============================

            else:

                total_skipped += 1

                results.append({
                    "company": company.name,
                    "ats_type": company.ats_type,
                    "status": "skipped",
                    "reason": (
                        f"Unsupported ATS: "
                        f"{company.ats_type}"
                    ),
                })

                continue

            # =============================
            # SUCCESS COUNTERS
            # =============================

            new_jobs = result.get(
                "total_new",
                0,
            )

            matching_jobs = result.get(
                "total_matches",
                0,
            )

            total_new_jobs += new_jobs
            total_matching_jobs += matching_jobs
            total_success += 1

            company.last_scanned_at = (
                datetime.utcnow()
            )

            company.initial_scan_complete = True

            results.append({
                "company": company.name,
                "ats_type": company.ats_type,
                "status": "success",
                "new_jobs": new_jobs,
                "matching_jobs": matching_jobs,
            })

        except Exception as e:

            total_errors += 1

            company.last_scanned_at = (
                datetime.utcnow()
            )

            results.append({
                "company": company.name,
                "ats_type": company.ats_type,
                "status": "error",
                "error": str(e),
            })

    db.commit()

    duration_seconds = round(
        time.perf_counter() - start_time,
        2,
    )

    return {
        "batch": batch,
        "batch_size": batch_size,
        "total_companies": total_companies,
        "companies_in_batch": len(companies),

        "companies_scanned": total_success,
        "companies_scanned_successfully": total_success,
        "companies_skipped": total_skipped,
        "companies_failed": total_errors,

        "new_jobs": total_new_jobs,
        "new_matches": total_matching_jobs,
        "matching_jobs": total_matching_jobs,

        "duration_seconds": duration_seconds,

        "results": results,
    }

@app.post("/companies/bulk-seed")
async def bulk_seed_companies(
    limit: int = 600,
    db: Session = Depends(get_db),
):
    catalog = await load_company_catalog(
        limit=limit
    )

    added = 0
    updated = 0
    skipped = 0
    duplicates_removed = 0

    existing_companies = (
        db.query(models.Company)
        .all()
    )

    company_by_name = {
        company.name.strip().lower(): company
        for company in existing_companies
    }

    seen_catalog_names = set()

    for item in catalog:
        name = item["name"].strip()
        normalized_name = name.lower()

        # Prevent duplicates inside the incoming catalog
        if normalized_name in seen_catalog_names:
            duplicates_removed += 1
            continue

        seen_catalog_names.add(
            normalized_name
        )

        existing = company_by_name.get(
            normalized_name
        )

        if existing:
            changed = False

            if (
                existing.ats_type
                != item["ats_type"]
            ):
                existing.ats_type = (
                    item["ats_type"]
                )
                changed = True

            if (
                existing.board_token
                != item["board_token"]
            ):
                existing.board_token = (
                    item["board_token"]
                )
                changed = True

            if (
                existing.career_url
                != item["career_url"]
            ):
                existing.career_url = (
                    item["career_url"]
                )
                changed = True

            if not existing.enabled:
                existing.enabled = True
                changed = True

            if changed:
                updated += 1
            else:
                skipped += 1

            continue

        company = models.Company(
            name=name,
            ats_type=item["ats_type"],
            board_token=item[
                "board_token"
            ],
            career_url=item[
                "career_url"
            ],
            enabled=True,
        )

        db.add(company)

        # IMPORTANT:
        # immediately register pending company
        # so another same-name item won't be added
        company_by_name[
            normalized_name
        ] = company

        added += 1

    try:
        db.commit()

    except Exception:
        db.rollback()
        raise

    return {
        "added": added,
        "updated": updated,
        "skipped": skipped,
        "duplicates_removed":
            duplicates_removed,
        "catalog_size": len(catalog),
        "database_total": (
            db.query(models.Company)
            .count()
        ),
    }


@app.put("/companies/{company_id}")
def update_company(
    company_id: int,
    ats_type: str,
    board_token: str,
    db: Session = Depends(get_db),
):
    company = (
        db.query(models.Company)
        .filter(models.Company.id == company_id)
        .first()
    )

    if not company:
        raise HTTPException(
            status_code=404,
            detail="Company not found",
        )

    company.ats_type = ats_type.lower()
    company.board_token = board_token

    db.commit()
    db.refresh(company)

    return company

@app.post("/test/telegram")
async def test_telegram():
    class TestJob:
        company = "Job Radar Test"
        title = "Machine Learning Engineer"
        location = "Bangalore, India"
        experience_min = 0
        experience_max = 2
        career_url = "https://example.com/job"

    success = await send_telegram_alert(
        TestJob()
    )

    return {
        "success": success
    }

@app.post("/companies/seed")
def seed_companies(
    db: Session = Depends(get_db),
):
    added = []
    skipped = []

    for company_data in SEED_COMPANIES:

        existing = (
            db.query(models.Company)
            .filter(
                models.Company.name
                == company_data["name"]
            )
            .first()
        )

        if existing:
            skipped.append(
                company_data["name"]
            )
            continue

        company = models.Company(
            name=company_data["name"],
            career_url=company_data["career_url"],
            ats_type=company_data["ats_type"],
            board_token=company_data["board_token"],
            enabled=company_data["enabled"],
        )

        db.add(company)
        added.append(
            company_data["name"]
        )

    db.commit()

    return {
        "added_count": len(added),
        "skipped_count": len(skipped),
        "added": added,
        "skipped": skipped,
    }

@app.get("/test/experience")
def test_experience(
    title: str = "",
    description: str = "",
):
    (
        experience_min,
        experience_max,
        experience_not_specified,
    ) = parse_experience(
        description,
        title,
    )

    return {
        "title": title,
        "experience_min": experience_min,
        "experience_max": experience_max,
        "experience_not_specified": experience_not_specified,
    }

@app.get("/test/role")
def test_role(
    title: str,
):
    return {
        "title": title,
        "role_category": detect_role(
            title
        ),
    }

@app.post("/jobs/reprocess")
def reprocess_jobs(
    db: Session = Depends(get_db),
):
    jobs = db.query(models.Job).all()

    updated = 0
    matched = 0

    for job in jobs:
        (
            experience_min,
            experience_max,
            experience_not_specified,
        ) = parse_experience(
            job.description or "",
            job.title or "",
        )

        role_category = detect_role(
            job.title
        )

        is_match = job_matches(
            title=job.title,
            location=job.location,
            min_experience=experience_min,
            max_experience=experience_max,
        )

        job.experience_min = experience_min
        job.experience_max = experience_max
        job.experience_not_specified = (
            experience_not_specified
        )

        job.role_category = role_category
        job.is_match = is_match

        updated += 1

        if is_match:
            matched += 1

    db.commit()

    return {
        "jobs_reprocessed": updated,
        "matching_jobs": matched,
    }

@app.post("/alerts/send-current-matches")
async def send_current_match_alerts(
    db: Session = Depends(get_db),
):
    jobs = (
        db.query(models.Job)
        .filter(models.Job.is_match == True)
        .all()
    )

    sent = 0
    failed = 0

    for job in jobs:
        success = await send_telegram_alert(
            job
        )

        if success:
            sent += 1
        else:
            failed += 1

    return {
        "matching_jobs": len(jobs),
        "alerts_sent": sent,
        "alerts_failed": failed,
    }

@app.get("/stats")
def get_stats(
    db: Session = Depends(get_db),
):
    total_jobs = db.query(models.Job).count()

    matching_jobs = (
        db.query(models.Job)
        .filter(models.Job.is_match == True)
        .count()
    )

    companies_monitored = (
        db.query(models.Company)
        .filter(models.Company.enabled == True)
        .count()
    )

    last_scanned_company = (
        db.query(models.Company)
        .filter(
            models.Company.last_scanned_at.isnot(None)
        )
        .order_by(
            models.Company.last_scanned_at.desc()
        )
        .first()
    )

    return {
        "total_jobs": total_jobs,
        "matching_jobs": matching_jobs,
        "companies_monitored": companies_monitored,
        "last_scan": (
            last_scanned_company.last_scanned_at
            if last_scanned_company
            else None
        ),
    }


@app.post("/jobs/{job_id}/apply")
def mark_job_as_applied(
    job_id: int,
    db: Session = Depends(get_db),
):
    job = (
        db.query(models.Job)
        .filter(models.Job.id == job_id)
        .first()
    )

    if not job:
        raise HTTPException(
            status_code=404,
            detail="Job not found",
        )

    existing_application = (
        db.query(models.Application)
        .filter(
            models.Application.job_id == job_id
        )
        .first()
    )

    if existing_application:
        return {
            "message": "Job already marked as applied",
            "application_id": existing_application.id,
        }

    application = models.Application(
        job_id=job_id,
        status="applied",
        result="Pending",
    )

    db.add(application)
    db.commit()
    db.refresh(application)

    return {
        "message": "Job marked as applied",
        "application_id": application.id,
        "job_id": job_id,
        "status": application.status,
    }

@app.get("/applications")
def get_applications(
    db: Session = Depends(get_db),
):
    applications = (
        db.query(models.Application)
        .order_by(
            models.Application.applied_at.desc()
        )
        .all()
    )

    results = []

    for application in applications:
        job = application.job

        results.append({
            "id": application.id,
            "job_id": application.job_id,
            "company": job.company,
            "title": job.title,
            "location": job.location,
            "career_url": job.career_url,
            "status": application.status,
            "result": application.result,
            "notes": application.notes,
            "applied_at": application.applied_at,
            "updated_at": application.updated_at,
        })

    return results

@app.put("/applications/{application_id}")
def update_application(
    application_id: int,
    status: str | None = None,
    result: str | None = None,
    notes: str | None = None,
    db: Session = Depends(get_db),
):
    application = (
        db.query(models.Application)
        .filter(
            models.Application.id
            == application_id
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    if status is not None:
        application.status = status

    if result is not None:
        application.result = result

    if notes is not None:
        application.notes = notes

    application.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(application)

    return {
        "message": "Application updated",
        "id": application.id,
        "status": application.status,
        "result": application.result,
        "notes": application.notes,
    }

@app.get("/applications/stats")
def get_application_stats(
    db: Session = Depends(get_db),
):
    applications = (
        db.query(models.Application)
        .all()
    )

    total = len(applications)

    counts = {
        "applied": 0,
        "assessment": 0,
        "interview": 0,
        "final_interview": 0,
        "offer": 0,
        "rejected": 0,
        "withdrawn": 0,
        "no_response": 0,
    }

    for application in applications:
        if application.status in counts:
            counts[application.status] += 1

    interviews = (
        counts["interview"]
        + counts["final_interview"]
    )

    interview_rate = (
        round(
            (interviews / total) * 100,
            1,
        )
        if total > 0
        else 0
    )

    offer_rate = (
        round(
            (counts["offer"] / total) * 100,
            1,
        )
        if total > 0
        else 0
    )

    return {
        "total_applications": total,
        **counts,
        "interview_rate": interview_rate,
        "offer_rate": offer_rate,
    }

@app.delete("/applications/{application_id}")
def delete_application(
    application_id: int,
    db: Session = Depends(get_db),
):
    application = (
        db.query(models.Application)
        .filter(
            models.Application.id == application_id
        )
        .first()
    )

    if not application:
        raise HTTPException(
            status_code=404,
            detail="Application not found",
        )

    db.delete(application)
    db.commit()

    return {
        "message": "Application removed",
        "application_id": application_id,
    }
    
