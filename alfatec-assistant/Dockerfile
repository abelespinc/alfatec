# Use the official Python 3.11 image
FROM python:3.11

# Set the working directory in the container
WORKDIR /app

# Install Poetry
RUN pip install poetry

# Copy the current directory contents into the container at /app
COPY . /app/

# Install the dependencies using Poetry, without creating a virtual environment
RUN poetry config virtualenvs.create false && poetry install --no-root

# Install Gunicorn for running the Flask app in production
RUN pip install gunicorn

# Create the logs directory
RUN mkdir -p /var/logs

# Expose port 8504
EXPOSE 8504

# Command to run the Flask application using Gunicorn
CMD ["hypercorn", "--bind", "0.0.0.0:8504", "app:app"]
