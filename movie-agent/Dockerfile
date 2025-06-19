# Use the official lightweight Python image.
# https://hub.docker.com/_/python
FROM python:3.9-slim-buster

# Allow statements and log messages to immediately appear in the Cloud Run logs
ENV PYTHONUNBUFFERED True

# Copy local code to the container image.
# Forcing copy rebuild for syntax error fix - try CACHE_BREAKER=9 if 8 fails for copy.
ARG CACHE_BREAKER_COPY=124
RUN echo "Cache buster for COPY: ${CACHE_BREAKER_COPY}"

WORKDIR /app
COPY . /app 

# Install production dependencies.
ARG CACHE_BREAKER=44
# RUN pip install google-generativeai
RUN pip install -r requirements.txt

# Run the web service on container startup.
# Specify the port Cloud Run will listen on.
ENV PORT 8080
CMD exec gunicorn --bind :$PORT --workers 1 --threads 8 --timeout 0 main:app