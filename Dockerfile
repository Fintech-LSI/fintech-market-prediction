# Use Python 3.11 as the base image
FROM python:3.11-slim

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

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make sure the model directory exists
RUN mkdir -p /app/model

# Copy the model files into the container
COPY model/model.pkl /app/model/model.pkl
COPY model/svm.pkl /app/model/svm.pkl

# Copy the current directory contents into the container at /app
COPY . .

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV FLASK_APP=service.py
ENV PYTHONUNBUFFERED=1
ENV TF_ENABLE_ONEDNN_OPTS=0

# Run Flask directly as specified
CMD ["flask", "--app", "service.py", "run", "--host=0.0.0.0"]