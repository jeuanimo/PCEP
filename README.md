# PCEP Prep Coach

A full-stack Django web application designed to prepare learners for the **PCEP-30-02 — Certified Entry-Level Python Programmer** certification exam. PCEP Prep Coach offers structured lessons, weighted quizzes, hands-on coding labs, flashcard review, and adaptive progress tracking — all aligned to the official PCEP exam blueprint.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Setup Instructions](#setup-instructions)
- [Migrations](#migrations)
- [Seed Data](#seed-data)
- [Creating a Superuser](#creating-a-superuser)
- [Running the Development Server](#running-the-development-server)
- [Screenshots](#screenshots)
- [PCEP Exam Domain Alignment](#pcep-exam-domain-alignment)
- [Roadmap](#roadmap)
- [Future Enhancements](#future-enhancements)
- [License](#license)

---

## Project Overview

PCEP Prep Coach is a self-study platform that mirrors the structure and weighting of the PCEP-30-02 exam. Rather than treating all topics equally, the app uses the **official exam domain weights** to prioritize practice where it matters most:

| Domain | Weight | Focus Area |
|--------|--------|------------|
| 1 — Computer Programming Fundamentals | 18% | Literals, variables, I/O, operators |
| 2 — Control Flow | 29% | Conditionals, loops, logic |
| 3 — Data Collections | 25% | Lists, tuples, dictionaries, strings |
| 4 — Functions & Exceptions | 28% | Defining functions, scopes, error handling |

Every quiz mode, readiness score, and recommendation engine respects these weights — so a student spending time in the app is spending it the same way the exam allocates its marks.

---

## Features

### Structured Learning
- **4 exam domains** and **22 topics** mapped to official PCEP-30-02 objectives
- Rich HTML lessons with code examples, organized by topic and difficulty
- Breadcrumb navigation from domain → topic → lesson

### Quizzes & Exam Simulation
- **6 question types**: multiple-choice, multiple-select, true/false, fill-in-the-blank, code output prediction, and short answer
- **4 quiz modes**: Topic (10 Qs), Domain (15 Qs), Mixed (20 Qs weighted), Full Exam (40 Qs weighted per PCEP blueprint)
- Per-question explanations revealed after submission
- Passing threshold of **70%** — matching the real PCEP exam
- Weak-area analysis that identifies topics needing more practice

### Coding Labs
- Hands-on coding challenges with starter code, progressive hints, and expected output
- **Sandboxed code execution**: AST validation → subprocess with CPU/memory resource limits → 10-second wall-clock timeout
- Output comparison against instructor-defined expected output
- Attempt history with error tracking and submitted code review
- **Solution reveal** after success or N failed attempts (configurable per challenge)
- Solution explanations with reference code for learning

### Flashcards
- Spaced-repetition-style flashcard review per topic
- User ratings (easy / medium / hard) influence review priority
- Hints available on each card

### Progress & Readiness Tracking
- **Adaptive confidence scoring** per topic — rises on correct answers, drops on incorrect, with diminishing returns
- Topic mastery levels: Not Started → Learning → Practicing → Mastered
- **Weighted readiness score**: exam readiness calculated as the weighted average of domain confidence, using all topics (not just started ones) for an honest assessment
- Study streak tracking (consecutive-day practice)
- Personalized dashboard with domain breakdown, recommendations, and recent activity

### Accounts & Profiles
- User registration, login/logout, profile management
- Avatar upload support
- Target exam date tracking
- Auto-created profiles via signals

---

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12+, Django 5.x |
| **Database** | SQLite (dev) / PostgreSQL (prod-ready via env vars) |
| **Frontend** | Bootstrap 5.3.3, Bootstrap Icons 1.11.3, vanilla JavaScript |
| **Code Sandbox** | Python `ast`, `multiprocessing`, `resource` (process isolation with CPU/memory limits) |
| **Image Uploads** | Pillow |

No heavyweight JavaScript frameworks — the frontend uses server-rendered Django templates with progressive enhancement via vanilla JS for AJAX submissions in quizzes and labs.

---

## Project Structure

```
PCEP/
├── manage.py
├── pcep_prep_coach/          # Django project settings
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── core/                     # Home page, seed_data command
├── accounts/                 # Auth, UserProfile, signals
├── learning/                 # Domains, Topics, Lessons, Flashcards
├── quizzes/                  # Questions, QuizAttempts, weighted selection
├── labs/                     # CodingChallenges, sandboxed execution
├── progress/                 # TopicProgress, StudySessions, readiness
├── templates/                # Project-level Django templates
│   ├── base.html
│   ├── accounts/
│   ├── core/
│   ├── labs/
│   ├── learning/
│   ├── progress/
│   └── quizzes/
├── static/
│   ├── css/style.css
│   ├── images/
│   └── js/
└── media/                    # User-uploaded files (avatars)
```

### App Architecture

| App | Purpose |
|-----|---------|
| `core` | Landing page, management commands (`seed_data`) |
| `accounts` | User auth, `UserProfile` model (streaks, readiness score, avatar) |
| `learning` | Domain → Topic → Lesson → Flashcard content hierarchy |
| `quizzes` | Question bank (6 types), `QuizAttempt`, `UserAnswer`, exam mode |
| `labs` | `CodingChallenge`, `CodingAttempt`, sandboxed code evaluation |
| `progress` | `TopicProgress`, `StudySession`, recommendation engine, dashboard |

---

## Setup Instructions

### Prerequisites

- Python 3.12 or higher
- pip
- (Optional) PostgreSQL for production

### 1. Clone the repository

```bash
git clone <repository-url>
cd PCEP
```

### 2. Create a virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install django pillow
```

### 4. Configure environment variables (optional)

For development, the defaults work out of the box. For production, set:

```bash
export DJANGO_SECRET_KEY="your-secure-secret-key"
export DJANGO_DEBUG=False
export DJANGO_ALLOWED_HOSTS="yourdomain.com,www.yourdomain.com"

# PostgreSQL (optional — SQLite used if these are unset)
export DB_ENGINE=django.db.backends.postgresql
export DB_NAME=pcep_coach
export DB_USER=your_db_user
export DB_PASSWORD=your_db_password
export DB_HOST=localhost
export DB_PORT=5432
```

> **Note:** In production (`DJANGO_DEBUG=False`), `DJANGO_SECRET_KEY` is **required** — the app will refuse to start without it.

---

## Migrations

Apply all database migrations:

```bash
python3 manage.py migrate
```

To check for any unapplied migrations:

```bash
python3 manage.py showmigrations
```

If you've made model changes:

```bash
python3 manage.py makemigrations
python3 manage.py migrate
```

---

## Seed Data

The project includes a management command that populates the database with comprehensive PCEP-30-02 content:

```bash
python3 manage.py seed_data
```

This creates:

- **4 exam domains** with official weights
- **22 topics** mapped to PCEP-30-02 objective codes (e.g., 1.1.1, 2.2.1)
- **44+ flashcards** covering key concepts
- **65+ quiz questions** across all 6 question types
- **15 coding challenges** with starter code, hints, and expected output

The command uses `update_or_create`, so it is **idempotent** — safe to run multiple times without creating duplicates.

---

## Creating a Superuser

To access the Django admin panel at `/admin/`:

```bash
python3 manage.py createsuperuser
```

Follow the prompts to set a username, email, and password.

---

## Running the Development Server

```bash
python3 manage.py runserver
```

Then visit:

- **App**: http://127.0.0.1:8000/
- **Admin**: http://127.0.0.1:8000/admin/

---

## Screenshots

> _Screenshots coming soon. This section will be updated with images of each major feature._

| Feature | Screenshot |
|---------|------------|
| Home Page | _placeholder_ |
| Learning — Domain List | _placeholder_ |
| Learning — Lesson Detail | _placeholder_ |
| Flashcard Review | _placeholder_ |
| Quiz — In Progress | _placeholder_ |
| Quiz — Results & Explanations | _placeholder_ |
| Coding Lab — Challenge Detail | _placeholder_ |
| Progress Dashboard | _placeholder_ |
| Profile Page | _placeholder_ |

---

## PCEP Exam Domain Alignment

PCEP Prep Coach is built around the official **PCEP-30-02 exam blueprint**. Here's how the app enforces alignment:

### Weighted Question Selection

When generating a Full Exam quiz (40 questions), the app selects questions proportionally:

| Domain | Weight | Questions (of 40) |
|--------|--------|--------------------|
| 1 — Fundamentals | 18% | ~7 |
| 2 — Control Flow | 29% | ~12 |
| 3 — Data Collections | 25% | ~10 |
| 4 — Functions & Exceptions | 28% | ~11 |

The `pick_weighted_questions()` service ensures this distribution, falling back gracefully when a domain has fewer questions than its quota.

### Weighted Readiness Score

The dashboard's readiness percentage isn't a simple average. It's calculated as:

```
readiness = Σ (domain_weight × domain_avg_confidence)
```

Where `domain_avg_confidence` averages across **all** topics in that domain — including topics the student hasn't started yet (counted as 0%). This prevents inflated readiness from only practicing easy topics.

### Adaptive Confidence

Each `TopicProgress` tracks a confidence score (0–100) that adapts with practice:

- **Correct answer**: confidence increases by `max(2, (100 - current) / 5)` — diminishing returns near mastery
- **Incorrect answer**: confidence decreases by `max(3, current / 8)` — bigger drops when confidence is high
- **Mastery thresholds**: Mastered ≥ 80, Practicing ≥ 40, Learning > 0 attempts

### Smart Recommendations

The recommendation engine analyzes weak areas by cross-referencing domain weights with current confidence levels, surfacing the topics where improvement would have the greatest impact on exam readiness.

---

## Roadmap

- [x] Domain / Topic / Lesson content structure
- [x] 6 question types with per-choice explanations
- [x] 4 quiz modes (topic, domain, mixed, full exam)
- [x] Weighted question selection matching PCEP blueprint
- [x] Sandboxed code execution with resource limits
- [x] Coding labs with progressive hints and solution reveal
- [x] Flashcard review with difficulty ratings
- [x] Adaptive confidence tracking per topic
- [x] Weighted readiness score
- [x] Study streak tracking
- [x] Personalized dashboard with recommendations
- [x] Seed data command with 22 topics, 65+ questions, 15 challenges
- [ ] Timed exam mode with countdown timer
- [ ] Spaced repetition scheduling for flashcards
- [ ] Code challenge difficulty auto-adjustment
- [ ] Export progress reports as PDF
- [ ] Social features (study groups, leaderboards)
- [ ] REST API for mobile client

---

## Future Enhancements

### Testing & Quality
- Comprehensive unit and integration test suite
- CI/CD pipeline with automated testing and linting

### Content Expansion
- Additional question banks contributed by instructors
- Community-submitted coding challenges with moderation
- Video lesson embeds per topic

### Infrastructure
- Docker containerization for one-command deployment
- Docker-based code sandbox (nsjail / Piston) for stronger isolation
- Celery task queue for async code evaluation
- Redis caching for readiness scores and quiz generation

### Learning Features
- Timed full exam simulation with question flagging and review
- Spaced repetition algorithm (SM-2) for flashcard scheduling
- Adaptive quiz difficulty based on rolling performance
- Code challenge auto-grading with partial credit (AST comparison)
- Peer code review for lab submissions

### Analytics
- Instructor dashboard with cohort analytics
- Study time tracking and study pattern insights
- Question difficulty calibration from aggregate pass rates

---

## License

This project is intended for educational purposes.
