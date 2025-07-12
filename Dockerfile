# Use a slim Python image
FROM python:3.10-slim AS base

# Set build argument for GitHub Access Key (Passed at build time)

# Set a dedicated working directory (not root)
WORKDIR /usr/src/app

### 🔹 SUBMODULE HANDLING (Using HTTPS with Token)

# Install git
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*


### 🔹 MAIN BUILD

# Install system dependencies for building
RUN apt-get update && apt-get install -y \
    build-essential  \
    libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy only requirements first for caching dependencies
COPY r.txt ./

# Install dependencies with no cache
RUN pip install -r r.txt

# Copy the rest of the project files into the working directory
COPY head_node .

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/usr/src/app:$PYTHONPATH \
    PORT=8080 \
    GCS_MOUNT_PATH=/mnt/bucket/ \
    RAY_RUNTIME_ENV_LOG_TO_DRIVER_ENABLED=1


# Copy the startup script

# Make the script executable

# Expose the application port
EXPOSE 8080

# Run Django using Gunicorn
CMD ["./main.py"]