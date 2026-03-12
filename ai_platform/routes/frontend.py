"""Serve the single-page HTML frontend."""
from flask import Blueprint, render_template

frontend_bp = Blueprint("frontend", __name__)


@frontend_bp.get("/")
def index():
    return render_template("index.html")


@frontend_bp.get("/jobs")
def jobs_page():
    return render_template("jobs.html")


@frontend_bp.get("/professionals")
def professionals_page():
    return render_template("professionals.html")


@frontend_bp.get("/dashboard")
def dashboard_page():
    return render_template("dashboard.html")
