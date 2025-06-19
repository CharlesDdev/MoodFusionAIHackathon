# Use the official Python image as a base image
FROM python:3.11-slim

# Set the working directory in the container
WORKDIR /app

# Install production dependencies.
# Copy requirements.txt separately to leverage Docker cache.
COPY requirements.txt .
ARG CACHE_BREAKER=11
RUN pip install --no-cache-dir -r requirements.txt

# Use a cache-busting argument for main.py updates
ARG CACHE_BREAKER_COPY=21
COPY main.py .

# Run the web service on container startup.
CMD ["python", "main.py"]