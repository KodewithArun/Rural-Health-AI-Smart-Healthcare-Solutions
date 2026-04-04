# Rural Health AI - Smart Healthcare Solution 🏥🤖

A comprehensive, Django-based web application providing a professional, friendly, and accurate AI health assistant tailored for rural communities. The system leverages an **Agentic RAG** (Retrieval-Augmented Generation) architecture using **LangGraph** for intelligent, multi-step reasoning. It seamlessly combines local medical document search with a robust web search fallback powered by **SerpAPI**, alongside full-featured telemedicine capabilities like appointment management, document uploads, and health awareness campaigns.

## 🌟 Key Features

- **Intelligent Healthcare Chatbot**: Context-aware AI assistant that answers health-related questions using a verified local document vector database (ChromaDB), resorting to real-time web search (SerpAPI) only when necessary.
- **Appointment Management**: Streamlined booking, updating, and cancellation of health appointments for both villagers and assigned health workers.
- **Awareness Campaigns**: Portal to distribute, track, and manage vital health awareness materials and campaigns.
- **Health Document Management**: Secure upload, parsing, and management of health-related documentation, which seamlessly feeds the AI's knowledge base.
- **Role-Based Access Control (RBAC)**: Distinct, secure portals and features for Villagers, Health Workers, and System Administrators.
- **Modern, Responsive UI**: Built with Tailwind CSS for accessible use across mobile and desktop devices.

## 🛠️ Tech Stack

- **Backend core**: Python, Django
- **AI & Agentic RAG**: LangChain, LangGraph, Google GenAI, SerpAPI
- **Vector Database**: ChromaDB (SQLite-based for local operations)
- **Frontend**: Django Templates, Tailwind CSS, Vanilla JS
- **Task Queue & Background Jobs**: Celery with Redis (for async operations)
- **Database**: PostgreSQL / SQLite (configurable)
- **Containerization**: Docker & Docker Compose

## 🚀 Getting Started (Docker / Recommended)

The easiest way to run the complete stack (including Redis, Celery, and the web app) is using Docker Compose.

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd Rural-Health-AI-Smart-Healthcare-Solutions
   ```

2. **Configure environment variables**
   Create a `.env` file in the project root:
   ```env
   # Django Settings
   SECRET_KEY=your_django_secret_key
   DEBUG=True

   # AI Agent Keys
   GOOGLE_GENAI_API_KEY=your_google_genai_api_key
   SERPAPI_API_KEY=your_serpapi_api_key
   
   # Email Settings (for notifications)
   EMAIL_HOST_USER=your_email@gmail.com
   EMAIL_HOST_PASSWORD=your_email_password
   ```

3. **Start the application**
   ```bash
   docker-compose up --build
   ```
   *The application will be accessible at `http://localhost:8000`.*

---

## 💻 Local Setup (Without Docker)

1. **Create and activate a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up the database and static files**
   ```bash
   python manage.py migrate
   python manage.py collectstatic
   ```

4. **Create a superuser (Admin account)**
   ```bash
   python manage.py createsuperuser
   ```

5. **Run the development server**
   ```bash
   python manage.py runserver
   ```

6. **Start Celery worker (Requires Redis running locally)**
   ```bash
   celery -A rural_health_assistant worker --beat --scheduler django --loglevel=info
   ```

---

## 🐳 Docker Guide for Developers

This project is fully containerized to ensure consistent development environments. The `docker-compose.yml` file defines the following services:
- **web**: The main Django application running via Gunicorn.
- **db**: A PostgreSQL 15 database instance.
- **redis**: An in-memory data store used as a broker and result backend for Celery.
- **celery_worker**: The asynchronous task queue processor.

### Common Docker Commands

- **Start all services in the background:**
  ```bash
  docker-compose up -d
  ```
  *(Note: You only need to add `--build` if you have added new packages to `requirements.txt` or changed the `Dockerfile`. Otherwise, standard code changes in your `.py` or `.html` files do not require a rebuild.)*

- **Stop all services:**
  ```bash
  docker-compose down
  ```

- **Stop services and delete the database volume (resets your DB):**
  ```bash
  docker-compose down -v
  ```

- **View logs across all services:**
  ```bash
  docker-compose logs -f
  ```

- **Run Django management commands inside the container:**
  ```bash
  docker-compose exec web python manage.py createsuperuser
  docker-compose exec web python manage.py makemigrations
  docker-compose exec web python manage.py shell
  ```

- **Access the PostgreSQL database shell directly:**
  ```bash
  docker-compose exec db psql -U postgres -d rural_health_assistant_db
  ```

---

## 📂 Project Structure

```text
├── accounts/               # User authentication, profiles, and RBAC
├── appointments/           # Appointment booking logic and models
├── awareness/              # Health awareness campaign management
├── chat/                   # Direct UI and history for the AI chatbot
├── contact/                # Contact and support functionalities
├── documents/              # Document upload and vector indexing
├── rag_components/         # Core AI logic: Agentic RAG, Vector store, LLM integration
├── vector_db/              # Local ChromaDB persistent storage
├── templates/              # Base and app-specific HTML templates
├── static/ & media/        # CSS, JS, Images, and uploaded user files
└── rural_health_assistant/ # Main Django configuration folder
```

## 📜 License & Credits

This project is intended for educational and non-commercial use to demonstrate AI applicability in rural healthcare solutions.

---
**Developed by Binisha Chapagain & Arun Pandey Laudari**  
*For BCA 6th Semester Final Project*
