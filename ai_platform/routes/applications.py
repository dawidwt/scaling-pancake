"""Application submission and management routes."""
from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models import Application, Job, Professional, Company, User

applications_bp = Blueprint("applications", __name__)


def _current_user() -> User | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


@applications_bp.post("/")
def apply():
    """Professional submits an application for a job."""
    user = _current_user()
    if not user or user.role != "professional":
        return jsonify({"error": "must be logged in as a professional"}), 401

    prof = user.professional
    data = request.get_json(silent=True) or {}
    job_id = data.get("job_id")

    if job_id is None:
        return jsonify({"error": "job_id is required"}), 400

    job = db.session.get(Job, job_id)
    if not job or job.status != "open":
        return jsonify({"error": "job not found or not open"}), 404

    # Prevent duplicate applications
    existing = Application.query.filter_by(
        job_id=job_id, professional_id=prof.id
    ).first()
    if existing:
        return jsonify({"error": "already applied to this job"}), 409

    application = Application(
        job_id=job_id,
        professional_id=prof.id,
        cover_letter=data.get("cover_letter", ""),
        proposed_rate=float(data["proposed_rate"]) if data.get("proposed_rate") is not None else None,
    )
    db.session.add(application)
    db.session.commit()
    return jsonify(application.to_dict()), 201


@applications_bp.get("/mine")
def my_applications():
    """List all applications for the logged-in professional."""
    user = _current_user()
    if not user or user.role != "professional":
        return jsonify({"error": "must be logged in as a professional"}), 401
    apps = Application.query.filter_by(professional_id=user.professional.id).all()
    return jsonify([a.to_dict() for a in apps])


@applications_bp.get("/job/<int:job_id>")
def applications_for_job(job_id: int):
    """List all applications for a job (company only)."""
    user = _current_user()
    if not user or user.role != "company":
        return jsonify({"error": "must be logged in as a company"}), 401

    job = db.get_or_404(Job, job_id)
    if job.company_id != user.company.id:
        return jsonify({"error": "forbidden"}), 403

    apps = Application.query.filter_by(job_id=job_id).all()
    return jsonify([a.to_dict() for a in apps])


@applications_bp.put("/<int:application_id>/status")
def update_status(application_id: int):
    """Company updates application status (reviewing/accepted/rejected)."""
    user = _current_user()
    if not user or user.role != "company":
        return jsonify({"error": "must be logged in as a company"}), 401

    app = db.get_or_404(Application, application_id)
    if app.job.company_id != user.company.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json(silent=True) or {}
    new_status = data.get("status", "")
    valid_statuses = ("pending", "reviewing", "accepted", "rejected")
    if new_status not in valid_statuses:
        return jsonify({"error": f"status must be one of {valid_statuses}"}), 400

    app.status = new_status
    db.session.commit()
    return jsonify(app.to_dict())


@applications_bp.get("/<int:application_id>")
def get_application(application_id: int):
    user = _current_user()
    if not user:
        return jsonify({"error": "not authenticated"}), 401

    app = db.get_or_404(Application, application_id)

    # Allow access to the applicant or the hiring company
    is_applicant = (
        user.role == "professional"
        and user.professional
        and app.professional_id == user.professional.id
    )
    is_company = (
        user.role == "company"
        and user.company
        and app.job.company_id == user.company.id
    )
    if not is_applicant and not is_company:
        return jsonify({"error": "forbidden"}), 403

    return jsonify(app.to_dict())
