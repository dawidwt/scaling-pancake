"""
Tests for the AI Training Talent Platform.
"""
import pytest
from ai_platform import create_app
from ai_platform.extensions import db as _db


@pytest.fixture
def app():
    app = create_app({
        "TESTING": True,
        "SQLALCHEMY_DATABASE_URI": "sqlite:///:memory:",
        "SECRET_KEY": "test-secret",
        "WTF_CSRF_ENABLED": False,
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


# ── Helpers ────────────────────────────────────────────────────────────────

def register_professional(client, email="pro@example.com", name="Alice Pro"):
    return client.post("/api/auth/register", json={
        "email": email, "password": "password123",
        "role": "professional", "name": name,
        "skills": ["NLP", "RLHF"], "hourly_rate": 50, "experience_years": 3,
    })


def register_company(client, email="co@example.com", name="AI Corp"):
    return client.post("/api/auth/register", json={
        "email": email, "password": "password123",
        "role": "company", "name": name,
        "description": "We build AI.", "website": "https://aicorp.example",
    })


def login(client, email, password="password123"):
    return client.post("/api/auth/login", json={"email": email, "password": password})


def post_job(client, **overrides):
    payload = {
        "title": "RLHF Feedback Specialist",
        "description": "Provide human feedback for model training.",
        "category": "RLHF Feedback",
        "required_skills": ["RLHF", "NLP"],
        "pay_rate": 45.0,
        "min_experience_years": 1,
        "remote": True,
    }
    payload.update(overrides)
    return client.post("/api/jobs/", json=payload)


# ── Auth tests ─────────────────────────────────────────────────────────────

class TestAuth:
    def test_register_professional(self, client):
        res = register_professional(client)
        assert res.status_code == 201
        data = res.get_json()
        assert data["user"]["role"] == "professional"
        assert data["user"]["email"] == "pro@example.com"

    def test_register_company(self, client):
        res = register_company(client)
        assert res.status_code == 201
        assert res.get_json()["user"]["role"] == "company"

    def test_register_duplicate_email(self, client):
        register_professional(client)
        res = register_professional(client)
        assert res.status_code == 409

    def test_register_invalid_role(self, client):
        res = client.post("/api/auth/register", json={
            "email": "x@x.com", "password": "pass", "role": "admin", "name": "X"
        })
        assert res.status_code == 400

    def test_login_success(self, client):
        register_professional(client)
        res = login(client, "pro@example.com")
        assert res.status_code == 200

    def test_login_wrong_password(self, client):
        register_professional(client)
        res = login(client, "pro@example.com", "wrongpass")
        assert res.status_code == 401

    def test_me_unauthenticated(self, client):
        res = client.get("/api/auth/me")
        assert res.status_code == 401

    def test_me_authenticated(self, client):
        register_professional(client)
        login(client, "pro@example.com")
        res = client.get("/api/auth/me")
        assert res.status_code == 200
        data = res.get_json()
        assert data["email"] == "pro@example.com"
        assert "profile" in data

    def test_logout(self, client):
        register_professional(client)
        login(client, "pro@example.com")
        client.post("/api/auth/logout")
        res = client.get("/api/auth/me")
        assert res.status_code == 401


# ── Professionals tests ────────────────────────────────────────────────────

class TestProfessionals:
    def test_list_professionals(self, client):
        register_professional(client)
        res = client.get("/api/professionals/")
        assert res.status_code == 200
        assert len(res.get_json()) == 1

    def test_get_professional(self, client):
        register_professional(client)
        pros = client.get("/api/professionals/").get_json()
        pid = pros[0]["id"]
        res = client.get(f"/api/professionals/{pid}")
        assert res.status_code == 200
        assert res.get_json()["name"] == "Alice Pro"

    def test_update_profile(self, client):
        register_professional(client)
        login(client, "pro@example.com")
        res = client.put("/api/professionals/me", json={
            "bio": "Expert in NLP.", "hourly_rate": 75, "availability": "available"
        })
        assert res.status_code == 200
        data = res.get_json()
        assert data["bio"] == "Expert in NLP."
        assert data["hourly_rate"] == 75.0

    def test_update_profile_unauthenticated(self, client):
        res = client.put("/api/professionals/me", json={"bio": "x"})
        assert res.status_code == 401

    def test_filter_by_skill(self, client):
        register_professional(client, "a@x.com", "Alice")
        register_professional(client, "b@x.com", "Bob")
        # Bob has no special skills in this fixture; both have RLHF from helper
        res = client.get("/api/professionals/?skill=NLP")
        assert res.status_code == 200
        assert len(res.get_json()) >= 1

    def test_submit_assessment(self, client):
        register_professional(client)
        login(client, "pro@example.com")
        res = client.post("/api/professionals/me/assessments", json={
            "skill": "RLHF", "score": 88
        })
        assert res.status_code == 201
        assert res.get_json()["score"] == 88.0

    def test_assessment_invalid_score(self, client):
        register_professional(client)
        login(client, "pro@example.com")
        res = client.post("/api/professionals/me/assessments", json={
            "skill": "RLHF", "score": 150
        })
        assert res.status_code == 400

    def test_assessment_upsert(self, client):
        """Resubmitting an assessment for the same skill updates the score."""
        register_professional(client)
        login(client, "pro@example.com")
        client.post("/api/professionals/me/assessments", json={"skill": "NLP", "score": 70})
        client.post("/api/professionals/me/assessments", json={"skill": "NLP", "score": 90})
        assessments = client.get("/api/professionals/me/assessments").get_json()
        nlp = [a for a in assessments if a["skill"] == "NLP"]
        assert len(nlp) == 1
        assert nlp[0]["score"] == 90.0


# ── Companies tests ────────────────────────────────────────────────────────

class TestCompanies:
    def test_list_companies(self, client):
        register_company(client)
        res = client.get("/api/companies/")
        assert res.status_code == 200
        assert len(res.get_json()) == 1

    def test_update_company(self, client):
        register_company(client)
        login(client, "co@example.com")
        res = client.put("/api/companies/me", json={"description": "Updated desc."})
        assert res.status_code == 200
        assert res.get_json()["description"] == "Updated desc."


# ── Jobs tests ─────────────────────────────────────────────────────────────

class TestJobs:
    def setup_company(self, client):
        register_company(client)
        login(client, "co@example.com")

    def test_create_job(self, client):
        self.setup_company(client)
        res = post_job(client)
        assert res.status_code == 201
        data = res.get_json()
        assert data["title"] == "RLHF Feedback Specialist"
        assert data["category"] == "RLHF Feedback"
        assert data["pay_rate"] == 45.0

    def test_create_job_invalid_category(self, client):
        self.setup_company(client)
        res = post_job(client, category="Made Up Category")
        assert res.status_code == 400

    def test_create_job_unauthenticated(self, client):
        res = post_job(client)
        assert res.status_code == 401

    def test_list_jobs(self, client):
        self.setup_company(client)
        post_job(client)
        post_job(client, title="Second Job", pay_rate=60)
        res = client.get("/api/jobs/")
        assert res.status_code == 200
        assert len(res.get_json()) == 2

    def test_filter_jobs_by_category(self, client):
        self.setup_company(client)
        post_job(client, category="RLHF Feedback")
        post_job(client, title="Annotation Job", category="Data Annotation", pay_rate=30)
        res = client.get("/api/jobs/?category=Data+Annotation")
        jobs = res.get_json()
        assert all(j["category"] == "Data Annotation" for j in jobs)

    def test_filter_jobs_by_min_pay(self, client):
        self.setup_company(client)
        post_job(client, pay_rate=20)
        post_job(client, title="High Pay", pay_rate=80)
        res = client.get("/api/jobs/?min_pay=50")
        jobs = res.get_json()
        assert all(j["pay_rate"] >= 50 for j in jobs)

    def test_update_job(self, client):
        self.setup_company(client)
        job_id = post_job(client).get_json()["id"]
        res = client.put(f"/api/jobs/{job_id}", json={"status": "closed"})
        assert res.status_code == 200
        assert res.get_json()["status"] == "closed"

    def test_update_job_forbidden(self, client):
        """A second company cannot update another company's job."""
        self.setup_company(client)
        job_id = post_job(client).get_json()["id"]
        # Register and log in as a different company
        register_company(client, "other@example.com", "Other Corp")
        login(client, "other@example.com")
        res = client.put(f"/api/jobs/{job_id}", json={"status": "closed"})
        assert res.status_code == 403

    def test_delete_job(self, client):
        self.setup_company(client)
        job_id = post_job(client).get_json()["id"]
        res = client.delete(f"/api/jobs/{job_id}")
        assert res.status_code == 200
        assert client.get(f"/api/jobs/{job_id}").status_code == 404

    def test_get_categories(self, client):
        res = client.get("/api/jobs/categories")
        assert res.status_code == 200
        cats = res.get_json()
        assert "RLHF Feedback" in cats
        assert "Data Annotation" in cats


# ── Applications tests ─────────────────────────────────────────────────────

class TestApplications:
    def setup_job(self, client):
        register_company(client)
        login(client, "co@example.com")
        job_id = post_job(client).get_json()["id"]
        client.post("/api/auth/logout")
        return job_id

    def test_apply_to_job(self, client):
        job_id = self.setup_job(client)
        register_professional(client)
        login(client, "pro@example.com")
        res = client.post("/api/applications/", json={
            "job_id": job_id, "cover_letter": "I love RLHF!", "proposed_rate": 42,
        })
        assert res.status_code == 201
        data = res.get_json()
        assert data["job_id"] == job_id
        assert data["status"] == "pending"

    def test_apply_duplicate(self, client):
        job_id = self.setup_job(client)
        register_professional(client)
        login(client, "pro@example.com")
        client.post("/api/applications/", json={"job_id": job_id})
        res = client.post("/api/applications/", json={"job_id": job_id})
        assert res.status_code == 409

    def test_apply_unauthenticated(self, client):
        job_id = self.setup_job(client)
        res = client.post("/api/applications/", json={"job_id": job_id})
        assert res.status_code == 401

    def test_my_applications(self, client):
        job_id = self.setup_job(client)
        register_professional(client)
        login(client, "pro@example.com")
        client.post("/api/applications/", json={"job_id": job_id})
        res = client.get("/api/applications/mine")
        assert res.status_code == 200
        assert len(res.get_json()) == 1

    def test_applications_for_job_by_company(self, client):
        job_id = self.setup_job(client)
        register_professional(client)
        login(client, "pro@example.com")
        client.post("/api/applications/", json={"job_id": job_id})
        client.post("/api/auth/logout")

        login(client, "co@example.com")
        res = client.get(f"/api/applications/job/{job_id}")
        assert res.status_code == 200
        assert len(res.get_json()) == 1

    def test_update_application_status(self, client):
        job_id = self.setup_job(client)
        register_professional(client)
        login(client, "pro@example.com")
        app_id = client.post("/api/applications/", json={"job_id": job_id}).get_json()["id"]
        client.post("/api/auth/logout")

        login(client, "co@example.com")
        res = client.put(f"/api/applications/{app_id}/status", json={"status": "accepted"})
        assert res.status_code == 200
        assert res.get_json()["status"] == "accepted"

    def test_update_status_invalid(self, client):
        job_id = self.setup_job(client)
        register_professional(client)
        login(client, "pro@example.com")
        app_id = client.post("/api/applications/", json={"job_id": job_id}).get_json()["id"]
        client.post("/api/auth/logout")

        login(client, "co@example.com")
        res = client.put(f"/api/applications/{app_id}/status", json={"status": "hired"})
        assert res.status_code == 400


# ── Frontend smoke tests ───────────────────────────────────────────────────

class TestFrontend:
    def test_index(self, client):
        assert client.get("/").status_code == 200

    def test_jobs_page(self, client):
        assert client.get("/jobs").status_code == 200

    def test_professionals_page(self, client):
        assert client.get("/professionals").status_code == 200

    def test_dashboard_page(self, client):
        assert client.get("/dashboard").status_code == 200
