# syntax=docker/dockerfile:1.7

# Use a slim Python base image
FROM python:3.12-slim AS base

# Set environment variables for Python
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set timezone
ENV TZ=Europe/Kyiv

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

ENV MONGODB_URL=""
ENV MONGODB_DATABASE_KSD=""
ENV MONGODB_DATABASE_KASDI=""

ENV OPENAI_API_KEY=""
ENV EMBEDDINGS_MODEL=""
ENV LLM_MODEL=""
ENV LLM_TEMPERATURE=""

ENV TELEGRAM_BOT_TOKEN=""

ENV TAVILY_API_KEY=""
ENV FIRE_CRAWL_API_KEY=""

ENV LANGSMITH_TRACING=true
ENV LANGSMITH_ENDPOINT=""
ENV LANGSMITH_API_KEY=""
ENV LANGSMITH_PROJECT=""


# Default command runs the Telegram bot
CMD ["python", "start_bot.py"]
