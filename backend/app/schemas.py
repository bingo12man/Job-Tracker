from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class JobCreate(BaseModel):
    company: str
    external_job_id: Optional[str] = None

    title: str
    location: Optional[str] = None
    description: Optional[str] = None

    career_url: str
    source: Optional[str] = None

    role_category: Optional[str] = None

    experience_min: Optional[float] = None
    experience_max: Optional[float] = None

    experience_not_specified: bool = False
    is_remote: bool = False

    posted_at: Optional[datetime] = None


class JobResponse(JobCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    is_match: bool
    first_seen_at: datetime

class CompanyCreate(BaseModel):
    name: str
    career_url: Optional[str] = None
    ats_type: str
    board_token: Optional[str] = None
    enabled: bool = True


class CompanyResponse(CompanyCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    last_scanned_at: Optional[datetime] = None
    created_at: datetime
    initial_scan_complete: bool