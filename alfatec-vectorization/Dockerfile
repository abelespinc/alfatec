# Base Image
FROM python:3.11

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y cron

# Copy existing project files including the virtual environment
COPY . /app/

# Ensure the virtual environment is recognized
ENV PATH="/app/env/bin:$PATH"

# Set up crontab (Executes vectorization script at 4 AM)
RUN echo "0 3 * * * /app/env/bin/python /app/scripts/vectorization.py" > /etc/cron.d/vectorization_cron \
    && chmod 0644 /etc/cron.d/vectorization_cron \
    && crontab /etc/cron.d/vectorization_cron

# Ensure cron logs exist
RUN touch /var/log/cron.log

# Expose ports
EXPOSE 8505 8506

# Start cron, Streamlit, and API
CMD ["/bin/bash", "-c", "cron && /app/env/bin/python -m streamlit run /app/streamlit_app/streamlit_dashboard.py --server.port=8505 --server.address=0.0.0.0 & /app/env/bin/uvicorn api:app --host 0.0.0.0 --port 8506"]