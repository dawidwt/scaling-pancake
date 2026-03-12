# TrainHire — AI Training Talent Platform

A marketplace for hiring professionals to help train AI models — similar to Mercor or micro1.

Companies post AI training tasks (data annotation, RLHF feedback, red teaming, model evaluation, etc.) and hire vetted professionals who apply directly.

---

## Features

### For Companies
- Register and create a company profile
- Post AI training jobs across 10 specialization categories
- Browse and manage applications (accept / reject / mark as reviewing)
- Close or delete job postings

### For Professionals
- Register with skills, hourly rate, and experience
- Browse and filter open jobs by category, skill, pay, and remote availability
- Apply to jobs with a cover letter and proposed rate
- Track application status from a personal dashboard
- Submit skill assessment scores to verify expertise

### Platform
- Session-based authentication (register / login / logout)
- REST JSON API for all operations
- Responsive web UI (no framework dependencies)
- SQLite database (swappable via `SQLALCHEMY_DATABASE_URI`)

---

## Job Categories

| Category | Description |
|---|---|
| Data Annotation | Label text, images, audio, and video |
| RLHF Feedback | Rank and rate model outputs for reinforcement learning |
| Model Evaluation | Test and benchmark model performance |
| Red Teaming | Probe models for harmful or unsafe behaviours |
| Content Review | Moderate AI-generated content |
| Code Review | Evaluate code quality and correctness in model outputs |
| Domain Expert Consultation | Provide specialist domain knowledge |
| Prompt Engineering | Design and optimize prompts |
| Synthetic Data Generation | Create training data at scale |
| Bias & Safety Auditing | Identify bias, fairness, and safety issues |

---

## Project Structure

```
scaling-pancake/
├── ai_platform/
│   ├── __init__.py          # App factory
│   ├── extensions.py        # Flask-SQLAlchemy instance
│   ├── models.py            # User, Professional, Company, Job, Application, Assessment
│   ├── routes/
│   │   ├── auth.py          # Register, login, logout, /me
│   │   ├── professionals.py # Profile CRUD + assessments
│   │   ├── companies.py     # Company profile CRUD
│   │   ├── jobs.py          # Job CRUD + filters
│   │   ├── applications.py  # Apply, review, status updates
│   │   └── frontend.py      # Serves HTML pages
│   ├── templates/
│   │   ├── base.html        # Navbar, modals, auth JS
│   │   ├── index.html       # Landing page
│   │   ├── jobs.html        # Job browser with filters
│   │   ├── professionals.html # Talent browser
│   │   └── dashboard.html   # Company & professional dashboards
│   └── static/
│       ├── css/style.css
│       └── js/auth.js
├── run.py                   # Entry point
└── tests/
    └── test_ai_platform.py  # 40 tests across all routes
```

---

## Requirements

- Python 3.10+
- Flask, Flask-SQLAlchemy, Werkzeug

Install dependencies:

```bash
pip install flask flask-sqlalchemy werkzeug
```

---

## Running

```bash
python run.py
```

Open [http://localhost:5000](http://localhost:5000).

---

## API Reference

### Auth

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/auth/register` | Register (role: `professional` \| `company`) |
| `POST` | `/api/auth/login` | Login |
| `POST` | `/api/auth/logout` | Logout |
| `GET` | `/api/auth/me` | Current user + profile |

### Jobs

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/jobs/` | List jobs (filters: `category`, `skill`, `min_pay`, `max_pay`, `remote_only`, `status`) |
| `POST` | `/api/jobs/` | Create job (company only) |
| `GET` | `/api/jobs/<id>` | Get job |
| `PUT` | `/api/jobs/<id>` | Update job (owning company) |
| `DELETE` | `/api/jobs/<id>` | Delete job (owning company) |
| `GET` | `/api/jobs/categories` | List all job categories |

### Professionals

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/professionals/` | List professionals (filters: `skill`, `availability`, `min_experience`, `max_rate`) |
| `GET` | `/api/professionals/<id>` | Get professional |
| `PUT` | `/api/professionals/me` | Update own profile |
| `POST` | `/api/professionals/me/assessments` | Submit skill score |
| `GET` | `/api/professionals/me/assessments` | My assessment scores |

### Applications

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/applications/` | Apply to a job (professional only) |
| `GET` | `/api/applications/mine` | My applications |
| `GET` | `/api/applications/job/<job_id>` | Applicants for a job (company only) |
| `PUT` | `/api/applications/<id>/status` | Update status: `pending` \| `reviewing` \| `accepted` \| `rejected` |
| `GET` | `/api/applications/<id>` | Get single application |

---

## Tests

```bash
pytest -v
```

40 tests covering auth, professionals, companies, jobs, applications, and frontend routes.
