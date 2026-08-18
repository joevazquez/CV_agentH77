from datetime import datetime
from typing import Optional

from pydantic import BaseModel, EmailStr


# ---------- Auth / Users ----------

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserOut(BaseModel):
    id: str
    email: EmailStr
    full_name: str

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


# ---------- CV ----------

class CVUpsert(BaseModel):
    raw_text: str
    skills: Optional[list[str]] = []
    summary: Optional[str] = None


class CVOut(BaseModel):
    id: str
    raw_text: str
    skills: list[str]
    summary: Optional[str]
    updated_at: datetime

    class Config:
        from_attributes = True


# ---------- Preferences ----------

class PreferenceUpsert(BaseModel):
    desired_roles: list[str] = []
    locations: list[str] = []
    remote_only: bool = False
    min_salary: Optional[float] = None
    industries: list[str] = []
    seniority: Optional[str] = None
    keywords_exclude: list[str] = []


class PreferenceOut(PreferenceUpsert):
    id: str

    class Config:
        from_attributes = True


# ---------- Jobs ----------

class JobOut(BaseModel):
    id: str
    source: str
    title: str
    company: Optional[str]
    location: Optional[str]
    description: str
    url: str
    salary_min: Optional[float]
    salary_max: Optional[float]
    remote: bool
    posted_at: Optional[datetime]

    class Config:
        from_attributes = True


class JobWithScoreOut(JobOut):
    score: float
    explanation: Optional[str]


# ---------- Matches ----------

class MatchOut(BaseModel):
    id: str
    job: JobOut
    score: float
    explanation: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Applications ----------

class ApplicationOut(BaseModel):
    id: str
    job_id: str
    tailored_cv: Optional[str]
    cover_letter: Optional[str]
    ready_to_send: bool
    submitted_by_user: bool
    created_at: datetime

    class Config:
        from_attributes = True


class ApplicationMarkSubmitted(BaseModel):
    submitted_by_user: bool = True


# ---------- Work Experience ----------

class WorkExperienceCreate(BaseModel):
    job_title: str
    company: str
    location: Optional[str] = None
    start_period: str
    end_period: Optional[str] = None
    description: str


class WorkExperienceOut(WorkExperienceCreate):
    id: str

    class Config:
        from_attributes = True
