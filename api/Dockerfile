# Use an official Python runtime as the base image
FROM python:3.9-slim

# Set the working directory in the container to /app
WORKDIR /api

# Copy the current directory contents into the container at /app
COPY . /api

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Run the Celery worker when the container launches
# CMD ["celery", "-A", "tasks", "worker", "--loglevel=info"]
EXPOSE 5001

CMD ["python", "app.py"]