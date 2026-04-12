# Use the official Python base image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies required for psycopg2, chromadb, etc.
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Install Python dependencies using uv for faster builds
COPY requirements.txt /app/
RUN pip install uv && \
    uv pip install --system -r requirements.txt

# Copy the project code into the container
COPY . /app/

# Create media and static directories
RUN mkdir -p /app/media /app/staticfiles

# Make sure to run the app on port 8000
EXPOSE 8000

# The command to run the application (override in docker-compose for celery)
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "rural_health_assistant.wsgi:application"]
