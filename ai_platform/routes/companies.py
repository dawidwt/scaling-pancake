"""Company profile routes."""
from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models import Company, User

companies_bp = Blueprint("companies", __name__)


def _current_company() -> Company | None:
    user_id = session.get("user_id")
    if not user_id:
        return None
    user = db.session.get(User, user_id)
    if not user or user.role != "company":
        return None
    return user.company


@companies_bp.get("/")
def list_companies():
    companies = Company.query.all()
    return jsonify([c.to_dict() for c in companies])


@companies_bp.get("/<int:company_id>")
def get_company(company_id: int):
    c = db.get_or_404(Company, company_id)
    return jsonify(c.to_dict())


@companies_bp.put("/me")
def update_company():
    company = _current_company()
    if not company:
        return jsonify({"error": "must be logged in as a company"}), 401

    data = request.get_json(silent=True) or {}
    for field in ("name", "description", "website", "industry", "logo_url"):
        if field in data:
            setattr(company, field, data[field])

    db.session.commit()
    return jsonify(company.to_dict())


@companies_bp.get("/me/jobs")
def my_jobs():
    company = _current_company()
    if not company:
        return jsonify({"error": "must be logged in as a company"}), 401
    return jsonify([j.to_dict() for j in company.jobs])
