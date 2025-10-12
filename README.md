# Rural-Health-AI-Smart-Healthcare-Solutions

A Django-based web application that provides a professional, friendly, and accurate health assistant chatbot for rural communities. The system leverages an **Agentic RAG** architecture using **LangGraph** for intelligent, multi-step reasoning. It combines local document search with a web search fallback powered by **SerpAPI**, and includes features like appointment management, document uploads, and awareness campaigns.

## Features

- **Healthcare Chatbot**: Answers health-related questions using local documents and web search (SerpAPI) as fallback.
- **Appointment Management**: Book, update, and cancel appointments for villagers and health workers.
- **Awareness Campaigns**: Share health awareness materials and campaigns.
- **Document Management**: Upload and manage health-related documents.
- **User Roles**: Supports villagers, health workers, and admins.
- **Modern UI**: Responsive design using Tailwind CSS.

## Tech Stack

- **Backend**: Django, Celery, PostgreSQL
- **Frontend**: Django Templates, Tailwind CSS
- **AI & RAG**: LangChain, LangGraph, ChromaDB, Google GenAI, SerpAPI
- **Task Queue**: Celery with Redis

## Setup Instructions

1. **Clone the repository**

    ```bash
    git clone <your-repo-url>
    cd Rural-Health-AI-Smart-Healthcare-Solutions
    ```

2. **Install dependencies**

    ```bash
    pip install -r requirements.txt
    ```

3. **Configure environment variables**

    Create a `.env` file in the project root and add:
    ```env
    SECRET_KEY=your_django_secret_key
    GOOGLE_GENAI_API_KEY=your_google_genai_api_key
    SERPAPI_API_KEY=your_serpapi_api_key
    EMAIL_HOST_USER=your_email@gmail.com
    EMAIL_HOST_PASSWORD=your_email_password
    ```

4. **Setup the database**

    ```bash
    python manage.py migrate
    ```

5. **Create a superuser**

    ```bash
    python manage.py createsuperuser
    ```

6. **Run the development server**

    ```bash
    python manage.py runserver
    ```

7. **Start Celery worker (for background tasks)**

    ```bash
    celery -A rural_health_assistant worker --beat --scheduler django --loglevel=info
    ```

## Folder Structure

- `accounts/` - User authentication and management
- `appointments/` - Appointment booking and management
- `awareness/` - Health awareness campaigns
- `chat/` - Chatbot logic and chat history
- `documents/` - Document upload and management
- `rag_components/` - RAG, LLM, and vector store logic
- `rural_health_assistant/` - Django project settings and URLs
- `templates/` - HTML templates
- `static/` - Static files (CSS, JS)
- `media/` - Uploaded files

## License

This project is for educational and non-commercial use only.

---

**Developed by Binisha Chapagain & Arun Pandey Laudari For BCA 6th Semester Final Project**
