# Use the official Python image as the base image
FROM python:3.8-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . /app

# Expose the port that the app will run on (replace with the port your Flask app uses)
EXPOSE 5000

# Define environment variables (optional)
# ENV FLASK_APP=app.py
# ENV FLASK_RUN_HOST=0.0.0.0

# Command to run the application (modify as needed)
CMD ["flask", "run", "--host=0.0.0.0"]
