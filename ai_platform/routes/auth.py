"""Authentication routes — register and login via session cookie."""
from flask import Blueprint, request, jsonify, session
from ..extensions import db
from ..models import User, Professional, Company

auth_bp = Blueprint("auth", __name__)


@auth_bp.post("/register")
def register():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")
    role = data.get("role", "")
    name = data.get("name", "").strip()

    if not email or not password or role not in ("professional", "company"):
        return jsonify({"error": "email, password, and role (professional|company) are required"}), 400
    if not name:
        return jsonify({"error": "name is required"}), 400
    if User.query.filter_by(email=email).first():
        return jsonify({"error": "email already registered"}), 409

    user = User(email=email, role=role)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()  # get user.id before committing

    if role == "professional":
        profile = Professional(user_id=user.id, name=name)
        profile.skills = data.get("skills", [])
        profile.hourly_rate = float(data.get("hourly_rate", 0))
        profile.experience_years = int(data.get("experience_years", 0))
        profile.location = data.get("location", "")
        db.session.add(profile)
    else:
        profile = Company(user_id=user.id, name=name)
        profile.description = data.get("description", "")
        profile.website = data.get("website", "")
        profile.industry = data.get("industry", "AI/ML")
        db.session.add(profile)

    db.session.commit()
    session["user_id"] = user.id
    return jsonify({"message": "registered", "user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip().lower()
    password = data.get("password", "")

    user = User.query.filter_by(email=email).first()
    if not user or not user.check_password(password):
        return jsonify({"error": "invalid credentials"}), 401

    session["user_id"] = user.id
    return jsonify({"message": "logged in", "user": user.to_dict()})


@auth_bp.post("/logout")
def logout():
    session.pop("user_id", None)
    return jsonify({"message": "logged out"})


@auth_bp.get("/me")
def me():
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "not authenticated"}), 401
    user = db.session.get(User, user_id)
    if not user:
        return jsonify({"error": "user not found"}), 404

    payload = user.to_dict()
    if user.role == "professional" and user.professional:
        payload["profile"] = user.professional.to_dict()
    elif user.role == "company" and user.company:
        payload["profile"] = user.company.to_dict()
    return jsonify(payload)
