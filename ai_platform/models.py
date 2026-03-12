"""
Database models for the AI Training Talent Platform.
"""
import json
from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from .extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)  # 'professional' | 'company' | 'admin'
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    professional = db.relationship("Professional", back_populates="user", uselist=False)
    company = db.relationship("Company", back_populates="user", uselist=False)

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)

    def to_dict(self) -> dict:
        return {"id": self.id, "email": self.email, "role": self.role}


class Professional(db.Model):
    __tablename__ = "professionals"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    bio = db.Column(db.Text, default="")
    hourly_rate = db.Column(db.Float, default=0.0)
    experience_years = db.Column(db.Integer, default=0)
    availability = db.Column(db.String(20), default="available")  # available | busy | unavailable
    _skills = db.Column("skills", db.Text, default="[]")  # JSON list
    location = db.Column(db.String(200), default="")
    linkedin_url = db.Column(db.String(500), default="")
    github_url = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="professional")
    applications = db.relationship("Application", back_populates="professional")
    assessments = db.relationship("Assessment", back_populates="professional")

    @property
    def skills(self) -> list:
        return json.loads(self._skills or "[]")

    @skills.setter
    def skills(self, value: list) -> None:
        self._skills = json.dumps(value)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "bio": self.bio,
            "hourly_rate": self.hourly_rate,
            "experience_years": self.experience_years,
            "availability": self.availability,
            "skills": self.skills,
            "location": self.location,
            "linkedin_url": self.linkedin_url,
            "github_url": self.github_url,
            "created_at": self.created_at.isoformat(),
            "assessment_scores": {a.skill: a.score for a in self.assessments},
        }


class Company(db.Model):
    __tablename__ = "companies"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, default="")
    website = db.Column(db.String(500), default="")
    industry = db.Column(db.String(100), default="AI/ML")
    logo_url = db.Column(db.String(500), default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", back_populates="company")
    jobs = db.relationship("Job", back_populates="company")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "name": self.name,
            "description": self.description,
            "website": self.website,
            "industry": self.industry,
            "logo_url": self.logo_url,
            "created_at": self.created_at.isoformat(),
            "open_jobs": sum(1 for j in self.jobs if j.status == "open"),
        }


class Job(db.Model):
    __tablename__ = "jobs"

    id = db.Column(db.Integer, primary_key=True)
    company_id = db.Column(db.Integer, db.ForeignKey("companies.id"), nullable=False)
    title = db.Column(db.String(300), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(100), nullable=False)  # see JOB_CATEGORIES
    _required_skills = db.Column("required_skills", db.Text, default="[]")
    pay_rate = db.Column(db.Float, nullable=False)  # USD per hour
    pay_type = db.Column(db.String(20), default="hourly")  # hourly | fixed
    min_experience_years = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default="open")  # open | closed | draft
    remote = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    deadline = db.Column(db.DateTime, nullable=True)

    company = db.relationship("Company", back_populates="jobs")
    applications = db.relationship("Application", back_populates="job")

    @property
    def required_skills(self) -> list:
        return json.loads(self._required_skills or "[]")

    @required_skills.setter
    def required_skills(self, value: list) -> None:
        self._required_skills = json.dumps(value)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "company_id": self.company_id,
            "company_name": self.company.name if self.company else None,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "required_skills": self.required_skills,
            "pay_rate": self.pay_rate,
            "pay_type": self.pay_type,
            "min_experience_years": self.min_experience_years,
            "status": self.status,
            "remote": self.remote,
            "created_at": self.created_at.isoformat(),
            "deadline": self.deadline.isoformat() if self.deadline else None,
            "application_count": len(self.applications),
        }


class Application(db.Model):
    __tablename__ = "applications"

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey("jobs.id"), nullable=False)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    status = db.Column(db.String(30), default="pending")  # pending | reviewing | accepted | rejected
    cover_letter = db.Column(db.Text, default="")
    proposed_rate = db.Column(db.Float, nullable=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc))

    job = db.relationship("Job", back_populates="applications")
    professional = db.relationship("Professional", back_populates="applications")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "job_id": self.job_id,
            "job_title": self.job.title if self.job else None,
            "professional_id": self.professional_id,
            "professional_name": self.professional.name if self.professional else None,
            "status": self.status,
            "cover_letter": self.cover_letter,
            "proposed_rate": self.proposed_rate,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }


class Assessment(db.Model):
    __tablename__ = "assessments"

    id = db.Column(db.Integer, primary_key=True)
    professional_id = db.Column(db.Integer, db.ForeignKey("professionals.id"), nullable=False)
    skill = db.Column(db.String(100), nullable=False)
    score = db.Column(db.Float, nullable=False)  # 0–100
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    professional = db.relationship("Professional", back_populates="assessments")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "professional_id": self.professional_id,
            "skill": self.skill,
            "score": self.score,
            "completed_at": self.completed_at.isoformat(),
        }


# ── Domain constants ──────────────────────────────────────────────────────────

JOB_CATEGORIES = [
    "Data Annotation",
    "RLHF Feedback",
    "Model Evaluation",
    "Red Teaming",
    "Content Review",
    "Code Review",
    "Domain Expert Consultation",
    "Prompt Engineering",
    "Synthetic Data Generation",
    "Bias & Safety Auditing",
]

SKILLS = [
    "Data Labeling",
    "NLP",
    "Computer Vision",
    "Python",
    "Machine Learning",
    "Prompt Engineering",
    "RLHF",
    "Content Moderation",
    "Code Review",
    "Medical Domain",
    "Legal Domain",
    "Finance Domain",
    "Scientific Research",
    "Multilingual",
    "Red Teaming",
    "AI Safety",
    "Data Analysis",
]
