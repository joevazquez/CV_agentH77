import enum
import uuid
from datetime import datetime

from sqlalchemy import (
    Column, String, Text, DateTime, ForeignKey, Float, Enum, JSON, Boolean
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.database import Base


def gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    cv = relationship("CV", back_populates="user", uselist=False, cascade="all, delete-orphan")
    preferences = relationship("Preference", back_populates="user", uselist=False, cascade="all, delete-orphan")
    matches = relationship("Match", back_populates="user", cascade="all, delete-orphan")


class CV(Base):
    __tablename__ = "cvs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, unique=True)
    raw_text = Column(Text, nullable=False)          # texto extraido del CV (PDF o pegado)
    skills = Column(JSON, default=list)               # lista de habilidades detectadas/declaradas
    summary = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="cv")


class Preference(Base):
    __tablename__ = "preferences"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False, unique=True)
    desired_roles = Column(JSON, default=list)        # ej ["Data Analyst", "Backend Developer"]
    locations = Column(JSON, default=list)             # ej ["Ciudad de Mexico", "Remoto"]
    remote_only = Column(Boolean, default=False)
    min_salary = Column(Float, nullable=True)
    industries = Column(JSON, default=list)
    seniority = Column(String, nullable=True)           # junior/mid/senior
    keywords_exclude = Column(JSON, default=list)       # palabras que descartan una vacante

    user = relationship("User", back_populates="preferences")


class JobStatus(str, enum.Enum):
    new = "new"
    matched = "matched"
    discarded = "discarded"


class Job(Base):
    __tablename__ = "jobs"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    source = Column(String, nullable=False)             # "adzuna", "manual", etc
    external_id = Column(String, index=True, nullable=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=True)
    location = Column(String, nullable=True)
    description = Column(Text, nullable=False)
    url = Column(String, nullable=False)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    remote = Column(Boolean, default=False)
    posted_at = Column(DateTime, nullable=True)
    fetched_at = Column(DateTime, default=datetime.utcnow)


class Match(Base):
    __tablename__ = "matches"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id"), nullable=False)
    score = Column(Float, nullable=False)                # 0-1 similitud
    explanation = Column(Text, nullable=True)
    status = Column(Enum(JobStatus), default=JobStatus.matched)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="matches")
    job = relationship("Job")


class Application(Base):
    __tablename__ = "applications"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    job_id = Column(UUID(as_uuid=False), ForeignKey("jobs.id"), nullable=False)
    tailored_cv = Column(Text, nullable=True)            # CV ajustado generado para esta vacante
    cover_letter = Column(Text, nullable=True)
    ready_to_send = Column(Boolean, default=False)        # queda lista para que el usuario la envie
    submitted_by_user = Column(Boolean, default=False)    # el usuario confirma que ya aplico manualmente
    created_at = Column(DateTime, default=datetime.utcnow)


class WorkExperience(Base):
    __tablename__ = "work_experiences"

    id = Column(UUID(as_uuid=False), primary_key=True, default=gen_uuid)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id"), nullable=False)
    job_title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, nullable=True)
    start_period = Column(String, nullable=False)     # texto libre, ej "Enero 2022"
    end_period = Column(String, nullable=True)          # vacio/None = "Actualidad"
    description = Column(Text, nullable=False)          # caracteristicas generales / logros
    created_at = Column(DateTime, default=datetime.utcnow)
