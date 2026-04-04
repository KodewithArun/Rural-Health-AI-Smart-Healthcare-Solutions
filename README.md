# Rural Health AI – Smart Healthcare Solution 🏥🤖

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](#)
[![Django](https://img.shields.io/badge/Django-Framework-0C4B33)](#)
[![Docker](https://img.shields.io/badge/Container-Docker-2496ED)](#)
[![License](https://img.shields.io/badge/License-Educational-lightgrey)](#)

An AI-enabled healthcare platform designed for underserved rural communities.  
It combines clinical guidance support, priority-based appointment scheduling, and role-secure workflows in one Django system.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Core Algorithms](#core-algorithms)
  - [1) Agentic RAG Algorithm](#1-agentic-rag-algorithm)
  - [2) Priority Appointment Scheduling Algorithm](#2-priority-appointment-scheduling-algorithm)
- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [Quick Start (Docker Recommended)](#quick-start-docker-recommended)
- [Local Development Setup](#local-development-setup)
- [Docker Developer Commands](#docker-developer-commands)
- [Project Structure](#project-structure)
- [Future Improvements](#future-improvements)
- [License](#license)
- [Authors](#authors)

---

## Project Overview

**Rural Health AI** addresses access barriers in rural healthcare by providing:

- AI-guided health Q&A with retrieval grounding
- Priority-aware appointment management for limited clinical resources
- Awareness campaign and document-driven knowledge workflows
- Role-based access for Villagers, Health Workers, and Admins

---

## Core Algorithms

### 1) Agentic RAG Algorithm

The chatbot follows a controlled multi-step reasoning pipeline:

1. **Semantic Retrieval**  
   Query embeddings are matched against verified health documents in **ChromaDB**.
2. **State-Based Decision Routing**  
   **LangGraph** decides whether local context is sufficient.
3. **Fallback Search**  
   If confidence is low, the system uses **SerpAPI** for fresh external context.
4. **Grounded Response Synthesis**  
   **Google GenAI** generates a contextual, safety-aware answer.

---

### 2) Priority Appointment Scheduling Algorithm

Appointment allocation is optimized by urgency and fairness, not only by first-come-first-served.

#### Scheduling flow

1. **Role & Access Validation**  
   Confirms request is from an allowed user role.
2. **Score Calculation**  
   Computes `PriorityScore` for each pending request.
3. **Queue Ordering**  
   Requests are sorted by score (high to low).
4. **Conflict-Free Slot Matching**  
   Assigns earliest feasible slot from provider availability.
5. **Escalation Rule**  
   If high-priority requests exceed SLA threshold, mark as escalated.
6. **Async Confirmation**  
   **Celery + Redis** handles notifications and status updates.
7. **Lifecycle Tracking**  
   Appointment states: `Scheduled`, `Completed`, `Cancelled`, `Escalated`.

---

## Key Features

- **AI Healthcare Assistant** (local-first RAG + fallback web retrieval)
- **Priority-Based Appointments** (triage-aware scheduling)
- **Role-Based Access Control (RBAC)** for Villager/Worker/Admin
- **Awareness Campaign Management**
- **Medical Document Upload + Indexing**
- **Responsive UI** with Tailwind CSS
- **Asynchronous Task Execution** with Celery

---

## Technology Stack

- **Backend:** Python, Django
- **AI/RAG:** LangChain, LangGraph, Google GenAI, SerpAPI
- **Vector Storage:** ChromaDB
- **Frontend:** Django Templates, Tailwind CSS, Vanilla JavaScript
- **Queue/Async:** Celery + Redis
- **Database:** PostgreSQL (default) / SQLite (dev option)
- **Containerization:** Docker + Docker Compose

---

## Quick Start (Docker Recommended)

### 1. Clone repository

```bash
git clone <your-repo-url>
cd Rural_Health_AI_Smart_Healthcare_Solution
```

### 2. Create `.env` file

```env
# Django
SECRET_KEY=your_django_secret_key
DEBUG=True

# AI Keys
GOOGLE_GENAI_API_KEY=your_google_genai_api_key
SERPAPI_API_KEY=your_serpapi_api_key

# Email (optional)
EMAIL_HOST_USER=your_email@gmail.com
EMAIL_HOST_PASSWORD=your_email_password
```

### 3. Build and run

```bash
docker-compose up --build
```

App URL: **http://localhost:8000**

---

## Local Development Setup

### Windows (PowerShell)

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py runserver
```

Start Celery worker:

```powershell
celery -A rural_health_assistant worker --beat --scheduler django --loglevel=info
```

### macOS/Linux

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
python manage.py createsuperuser
python manage.py runserver
```

---

## Docker Developer Commands

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Stop + remove volumes (DB reset)
docker-compose down -v

# Tail logs
docker-compose logs -f

# Django commands inside web container
docker-compose exec web python manage.py makemigrations
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser

# PostgreSQL shell
docker-compose exec db psql -U postgres -d rural_health_assistant_db
```

---

## Project Structure

```text
accounts/                 # Authentication, profiles, roles
appointments/             # Priority scheduling and booking logic
awareness/                # Awareness campaigns
chat/                     # Chat interface and conversation handling
contact/                  # Support/contact workflows
documents/                # Upload, parsing, indexing pipelines
rag_components/           # Agentic RAG graph, retrieval, generation
vector_db/                # Persistent ChromaDB storage
templates/                # Shared and app templates
static/                   # CSS/JS/static assets
media/                    # Uploaded files
rural_health_assistant/   # Django settings, URLs, WSGI/ASGI
```

---

## Future Improvements

- Explainable priority breakdown in UI (why a case was ranked high)
- Offline-first mobile mode for low-connectivity regions
- Multilingual support for local languages
- Model monitoring and response quality analytics

---

## License

Educational and non-commercial use.

---

## Authors

**Binisha Chapagain**  
**Arun Pandey Laudari**

BCA 6th Semester Final Project