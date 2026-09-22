from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text

from .database import Base
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from datetime import datetime
from sqlalchemy.orm import relationship

class Job(Base):
    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)

    company = Column(String, nullable=False)

    external_job_id = Column(
        String,
        nullable=True,
        index=True,
    )

    title = Column(
        String,
        nullable=False,
        index=True,
    )

    location = Column(
        String,
        nullable=True,
    )

    description = Column(
        Text,
        nullable=True,
    )

    career_url = Column(
        String,
        nullable=False,
        unique=True,
    )

    source = Column(
        String,
        nullable=True,
    )

    role_category = Column(
        String,
        nullable=True,
    )

    experience_min = Column(
        Float,
        nullable=True,
    )

    experience_max = Column(
        Float,
        nullable=True,
    )

    experience_not_specified = Column(
        Boolean,
        default=False,
    )

    is_remote = Column(
        Boolean,
        default=False,
    )

    is_match = Column(
        Boolean,
        default=False,
    )

    posted_at = Column(
        DateTime,
        nullable=True,
    )

    first_seen_at = Column(
        DateTime,
        default=datetime.utcnow,
    )
    application = relationship(
        "Application",
        backref="job",
        uselist=False,
        cascade="all, delete-orphan",
    )

class Company(Base):
    __tablename__ = "companies"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
        unique=True,
    )

    career_url = Column(
        String,
        nullable=True,
    )

    ats_type = Column(
        String,
        nullable=False,
    )

    board_token = Column(
        String,
        nullable=True,
    )

    enabled = Column(
        Boolean,
        default=True,
    )

    last_scanned_at = Column(
        DateTime,
        nullable=True,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
    )

    initial_scan_complete = Column(
    Boolean,
    default=False,
    )


class Application(Base):
    __tablename__ = "applications"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    job_id = Column(
        Integer,
        ForeignKey("jobs.id"),
        unique=True,
        nullable=False,
    )

    status = Column(
        String,
        default="applied",
        nullable=False,
    )

    applied_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    updated_at = Column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )

    notes = Column(
        Text,
        nullable=True,
    )

    result = Column(
        String,
        nullable=True,
    )