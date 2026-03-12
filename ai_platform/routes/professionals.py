"""Professionals CRUD + skill assessment routes."""
from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models import Professional, Assessment, User

professionals_bp = Blueprint("professionals", __name__)


def _current_professional() -> Professional | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user or user.role != "professional":
        return None
    return user.professional


@professionals_bp.get("/")
def list_professionals():
    """List professionals with optional filters."""
    skill_filter = request.args.get("skill", "").strip()
    availability = request.args.get("availability", "").strip()
    min_experience = request.args.get("min_experience", type=int)
    max_rate = request.args.get("max_rate", type=float)

    query = Professional.query
    if availability:
        query = query.filter_by(availability=availability)
    if min_experience is not None:
        query = query.filter(Professional.experience_years >= min_experience)
    if max_rate is not None:
        query = query.filter(Professional.hourly_rate <= max_rate)

    professionals = query.all()

    # Post-filter by skill (stored as JSON)
    if skill_filter:
        skill_lower = skill_filter.lower()
        professionals = [
            p for p in professionals
            if any(skill_lower in s.lower() for s in p.skills)
        ]

    return jsonify([p.to_dict() for p in professionals])


@professionals_bp.get("/<int:professional_id>")
def get_professional(professional_id: int):
    p = db.get_or_404(Professional, professional_id)
    return jsonify(p.to_dict())


@professionals_bp.put("/me")
def update_profile():
    prof = _current_professional()
    if not prof:
        return jsonify({"error": "must be logged in as a professional"}), 401

    data = request.get_json(silent=True) or {}
    for field in ("name", "bio", "location", "linkedin_url", "github_url", "availability"):
        if field in data:
            setattr(prof, field, data[field])
    if "hourly_rate" in data:
        prof.hourly_rate = float(data["hourly_rate"])
    if "experience_years" in data:
        prof.experience_years = int(data["experience_years"])
    if "skills" in data:
        prof.skills = list(data["skills"])

    db.session.commit()
    return jsonify(prof.to_dict())


@professionals_bp.post("/me/assessments")
def submit_assessment():
    """Record a skill assessment score for the logged-in professional."""
    prof = _current_professional()
    if not prof:
        return jsonify({"error": "must be logged in as a professional"}), 401

    data = request.get_json(silent=True) or {}
    skill = data.get("skill", "").strip()
    score = data.get("score")

    if not skill:
        return jsonify({"error": "skill is required"}), 400
    if score is None or not (0 <= float(score) <= 100):
        return jsonify({"error": "score must be between 0 and 100"}), 400

    # Upsert: replace existing assessment for the same skill
    existing = Assessment.query.filter_by(
        professional_id=prof.id, skill=skill
    ).first()
    if existing:
        existing.score = float(score)
        assessment = existing
    else:
        assessment = Assessment(
            professional_id=prof.id,
            skill=skill,
            score=float(score),
        )
        db.session.add(assessment)

    db.session.commit()
    return jsonify(assessment.to_dict()), 201


@professionals_bp.get("/me/assessments")
def get_my_assessments():
    prof = _current_professional()
    if not prof:
        return jsonify({"error": "must be logged in as a professional"}), 401
    return jsonify([a.to_dict() for a in prof.assessments])
