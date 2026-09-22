from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from . import models
from .database import SessionLocal
from .scanner import (
    scan_greenhouse_company,
    scan_lever_company,
    scan_ashby_company,
    scan_smartrecruiters_company,
    scan_workday_company,
)


scheduler = AsyncIOScheduler()


async def scheduled_scan():
    db = SessionLocal()

    try:
        companies = (
            db.query(models.Company)
            .filter(models.Company.enabled == True)
            .all()
        )

        for company in companies:

            try:
                send_alerts = company.initial_scan_complete

                # -------------------------
                # GREENHOUSE
                # -------------------------
                if company.ats_type == "greenhouse":

                    if not company.board_token:
                        print(
                            f"Skipping {company.name}: "
                            f"missing Greenhouse board token"
                        )
                        continue

                    result = await scan_greenhouse_company(
                        db=db,
                        company_name=company.name,
                        board_token=company.board_token,
                        send_alerts=send_alerts,
                    )

                # -------------------------
                # LEVER
                # -------------------------
                elif company.ats_type == "lever":

                    if not company.board_token:
                        print(
                            f"Skipping {company.name}: "
                            f"missing Lever company token"
                        )
                        continue

                    result = await scan_lever_company(
                        db=db,
                        company_name=company.name,
                        company_token=company.board_token,
                        send_alerts=send_alerts,
                    )

                # -------------------------
                # ASHBY
                # -------------------------
                elif company.ats_type == "ashby":

                    if not company.board_token:
                        print(
                            f"Skipping {company.name}: "
                            f"missing Ashby board token"
                        )
                        continue

                    result = await scan_ashby_company(
                        db=db,
                        company_name=company.name,
                        board_token=company.board_token,
                        send_alerts=send_alerts,
                    )
                elif company.ats_type == "smartrecruiters":

                    if not company.board_token:
                        print(
                            f"Skipping {company.name}: "
                            f"missing SmartRecruiters identifier"
                        )
                        continue

                    result = (
                        await scan_smartrecruiters_company(
                            db=db,
                            company_name=company.name,
                            company_identifier=(
                                company.board_token
                            ),
                            send_alerts=send_alerts,
                        )
                    )

                elif company.ats_type == "workday":

                    if not company.career_url:
                        print(
                            f"Skipping {company.name}: "
                            f"missing Workday career URL"
                        )
                        continue

                    result = await scan_workday_company(
                        db=db,
                        company_name=company.name,
                        career_url=company.career_url,
                        send_alerts=send_alerts,
                    )

                # -------------------------
                # UNSUPPORTED ATS
                # -------------------------
                else:
                    print(
                        f"Skipping {company.name}: "
                        f"unsupported ATS "
                        f"'{company.ats_type}'"
                    )
                    continue

                # -------------------------
                # SUCCESS
                # -------------------------
                company.last_scanned_at = datetime.utcnow()
                company.initial_scan_complete = True

                db.commit()

                print(
                    f"[SCAN] {company.name} | "
                    f"new={result['total_new']} | "
                    f"matches={result['total_matches']} | "
                    f"alerts={'ON' if send_alerts else 'OFF'}"
                )

            except Exception as e:
                db.rollback()

                print(
                    f"Scan failed for "
                    f"{company.name}: {e}"
                )

    finally:
        db.close()


def start_scheduler():

    if scheduler.running:
        return

    scheduler.add_job(
        scheduled_scan,
        trigger="interval",
        minutes=15,
        id="job_radar_scan",
        replace_existing=True,
    )

    scheduler.start()

    print(
        "Job Radar scheduler started. "
        "Scanning every 15 minutes."
    )