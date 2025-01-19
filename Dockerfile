# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    python3-dev \
    libgomp1 && \
    rm -rf /var/lib/apt/lists/*

# Copy the requirements file into the container
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the current directory contents into the container at /app
COPY . .

# Make sure the model directory exists
RUN mkdir -p /app/model

# Copy the model files into the container
COPY model/model.pkl /app/model/model.pkl
COPY model/svm.pkl /app/model/svm.pkl

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=main.py

# Run gunicorn to serve the application
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "main:app"]