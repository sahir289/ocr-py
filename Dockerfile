# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV AWS_REGION=us-east-1

# Set the working directory in the container
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3-venv \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy the current directory contents into the container at /app
COPY . /app

# Install the dependencies
RUN python3 -m venv venv
RUN ./venv/bin/pip install --no-cache-dir -r requirements.txt

# Expose the port that FastAPI will run on
EXPOSE 8000

# Run your Python script (replace `main.py` with your actual main script name)
CMD ["./venv/bin/python", "main.py"]