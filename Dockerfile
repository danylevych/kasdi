# syntax=docker/dockerfile:1.7

# Use a slim Python base image
FROM python:3.12-slim AS base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set timezone
ENV TZ=Europe/Kyiv

# Install minimal OS packages (certs, locales, and runtime basics)
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       ca-certificates \
       tzdata \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy dependency manifest first for better caching
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --upgrade pip \
    && pip install -r requirements.txt

# Copy the source code
COPY . .

# The bot expects to be run from the kasdi/ directory (relative imports like `from dependencies import ...`)
WORKDIR /app/kasdi

# Default command runs the Telegram bot
CMD ["python", "start_bot.py"]
