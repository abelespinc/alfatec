# Base Image
FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y cron

# Copy dependencies files
COPY pyproject.toml poetry.lock ./

# Install Poetry (for dependency management)
RUN pip install poetry \
    && poetry config virtualenvs.create false \
    && poetry install --no-root

# Create virtual environment manually
RUN python -m venv env

# Install dependencies inside the virtual environment
RUN /app/env/bin/pip install --upgrade pip \
    && /app/env/bin/pip install -r <(poetry export --without-hashes --format=requirements.txt)

# Install FastAPI and Uvicorn
RUN /app/env/bin/pip install fastapi uvicorn

# Copy the rest of the project files
COPY . .

# Set up crontab
RUN echo "0 5 * * * /app/env/bin/python /app/scripts/vectorization.py" > /etc/cron.d/vectorization_cron \
    && chmod 0644 /etc/cron.d/vectorization_cron \
    && crontab /etc/cron.d/vectorization_cron

# Ensure cron logs exist
RUN touch /var/log/cron.log

# Expose ports
EXPOSE 8505 8506

# Start cron, Streamlit, and API
CMD ["/bin/bash", "-c", "cron && /app/env/bin/python -m streamlit run /app/streamlit_app/streamlit_dashboard.py --server.port=8505 --server.address=0.0.0.0 & /app/env/bin/uvicorn api:app --host 0.0.0.0 --port 8506"]
