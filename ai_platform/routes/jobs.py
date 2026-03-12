"""Job posting CRUD routes."""
from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models import Job, Company, User, JOB_CATEGORIES

jobs_bp = Blueprint("jobs", __name__)


def _current_company() -> Company | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user or user.role != "company":
        return None
    return user.company


@jobs_bp.get("/")
def list_jobs():
    """List open jobs with optional filters."""
    category = request.args.get("category", "").strip()
    skill = request.args.get("skill", "").strip()
    min_pay = request.args.get("min_pay", type=float)
    max_pay = request.args.get("max_pay", type=float)
    remote_only = request.args.get("remote_only", "").lower() == "true"
    status_filter = request.args.get("status", "open")

    query = Job.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if category:
        query = query.filter(Job.category.ilike(f"%{category}%"))
    if min_pay is not None:
        query = query.filter(Job.pay_rate >= min_pay)
    if max_pay is not None:
        query = query.filter(Job.pay_rate <= max_pay)
    if remote_only:
        query = query.filter_by(remote=True)

    jobs = query.order_by(Job.created_at.desc()).all()

    if skill:
        skill_lower = skill.lower()
        jobs = [j for j in jobs if any(skill_lower in s.lower() for s in j.required_skills)]

    return jsonify([j.to_dict() for j in jobs])


@jobs_bp.get("/categories")
def get_categories():
    return jsonify(JOB_CATEGORIES)


@jobs_bp.get("/<int:job_id>")
def get_job(job_id: int):
    job = db.get_or_404(Job, job_id)
    return jsonify(job.to_dict())


@jobs_bp.post("/")
def create_job():
    company = _current_company()
    if not company:
        return jsonify({"error": "must be logged in as a company"}), 401

    data = request.get_json(silent=True) or {}
    title = data.get("title", "").strip()
    description = data.get("description", "").strip()
    category = data.get("category", "").strip()
    pay_rate = data.get("pay_rate")

    if not title or not description or not category:
        return jsonify({"error": "title, description, and category are required"}), 400
    if category not in JOB_CATEGORIES:
        return jsonify({"error": f"category must be one of: {JOB_CATEGORIES}"}), 400
    if pay_rate is None:
        return jsonify({"error": "pay_rate is required"}), 400

    job = Job(
        company_id=company.id,
        title=title,
        description=description,
        category=category,
        pay_rate=float(pay_rate),
        pay_type=data.get("pay_type", "hourly"),
        min_experience_years=int(data.get("min_experience_years", 0)),
        status=data.get("status", "open"),
        remote=bool(data.get("remote", True)),
    )
    job.required_skills = data.get("required_skills", [])

    db.session.add(job)
    db.session.commit()
    return jsonify(job.to_dict()), 201


@jobs_bp.put("/<int:job_id>")
def update_job(job_id: int):
    company = _current_company()
    if not company:
        return jsonify({"error": "must be logged in as a company"}), 401

    job = db.get_or_404(Job, job_id)
    if job.company_id != company.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}
    for field in ("title", "description", "pay_type", "status"):
        if field in data:
            setattr(job, field, data[field])
    if "category" in data:
        if data["category"] not in JOB_CATEGORIES:
            return jsonify({"error": "invalid category"}), 400
        job.category = data["category"]
    if "pay_rate" in data:
        job.pay_rate = float(data["pay_rate"])
    if "min_experience_years" in data:
        job.min_experience_years = int(data["min_experience_years"])
    if "remote" in data:
        job.remote = bool(data["remote"])
    if "required_skills" in data:
        job.required_skills = list(data["required_skills"])

    db.session.commit()
    return jsonify(job.to_dict())


@jobs_bp.delete("/<int:job_id>")
def delete_job(job_id: int):
    company = _current_company()
    if not company:
        return jsonify({"error": "must be logged in as a company"}), 401

    job = db.get_or_404(Job, job_id)
    if job.company_id != company.id:
        return jsonify({"error": "forbidden"}), 403

    db.session.delete(job)
    db.session.commit()
    return jsonify({"message": "deleted"})
