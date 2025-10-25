# KaSDi

A modular Telegram assistant with MongoDB (Beanie), LangChain/LangGraph agent, and Pinecone vector store. Designed to evolve into a full web/API app.

## Features
- Telegram bot (aiogram) with modular routers (commands, profile, books, kasdi agent)
- MongoDB via Beanie ODM (KSD and KaSDi domains)
- LangChain/LangGraph based agent with tools (search, scrape, memory)
- Vector store integration (Pinecone) and ingestion pipeline
- Config and logging utilities

## Project structure
```
kasdi/
  bot/
    routers/
    parsers/
    filters/
  chains/
    kasdi/
    tools/
  controllers/
  core/
  database/
  services/
  start_bot.py
```

> Note: Exact structure may evolve; see source for details.

## Prerequisites
- Python 3.12
- MongoDB
- Pinecone account + index
- OpenAI API key (for embeddings and/or Whisper)

## Quick start (local)
1) Create a virtual environment and install deps
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
2) Configure env vars (copy then edit)
```bash
cp .env.example kasdi/.env
```
3) Run bot
```bash
cd kasdi
python start_bot.py
```

## Docker
Build and run the bot in Docker:
```bash
docker build -t kasdi-bot:latest .
# if your env is at ./kasdi/.env
docker run --rm -it --env-file ./kasdi/.env kasdi-bot:latest
```

## Bot flows
High-level flow of user interactions:

- /start registers or updates the user
- Profile lets users add/edit personal instruction
- Books flow collects read books, parses entries, and links to KSD items
- Kasdi chat uses the agent to respond with context

## Configuration
Environment variables are loaded via `core/configs.py`. See `.env.example` for the full list:
- Database: `MONGODB_URL`, `MONGODB_DATABASE_KSD`, `MONGODB_DATABASE_KASDI`
- LLM: `OPENAI_API_KEY`, `LLM_MODEL`, `LLM_TEMPERATURE`, `EMBEDDINGS_MODEL`
- Pinecone: `PINECONE_API_KEY`, `PINECONE_INDEX_NAME`
- Telegram: `TELEGRAM_BOT_TOKEN`, `TELEGRAM_WEBHOOK_URL`
- Web tools: `TAVILY_API_KEY`, `FIRE_CRAWL_API_KEY`

## Logging
The project uses a scoped logger utility (`core/logger.py`). You can control verbosity via `LOG_LEVEL` in env. Key components include:
- Startup: `kasdi.start_bot`, `kasdi.bot`
- Routers: `kasdi.bot.routers.*`
- DB init: `kasdi.database.client`
- Dependencies: `kasdi.dependencies`

## Development
- Linting/formatting: consider ruff + black
- Typing: mypy for stricter checks
- Tests: add unit tests for controllers/services and integration tests with a test Mongo

## Roadmap
- FastAPI HTTP API with routes for user, chat, books
- Separate service layer and DTOs for API
- Improve ingestion with batching and retries
- Deploy with docker-compose (MongoDB + Bot + future API)

## Deployment to Azure AKS

See detailed guide: [docs/DEPLOYMENT_AKS.md](./docs/DEPLOYMENT_AKS.md)

Quick start:
```bash
# Create Azure resources
az aks create --resource-group kasdi-rg --name kasdi-aks --attach-acr kasdiacr

# Deploy
kubectl apply -f k8s/
```

CI/CD via GitHub Actions is configured in `.github/workflows/deploy-aks.yml` - push to `main` for auto-deploy.

## Quick Commands

See [docs/COMMANDS.md](./docs/COMMANDS.md) for full reference.

## Troubleshooting
- Bot doesn't start: check `TELEGRAM_BOT_TOKEN` and network access
- DB init errors: verify `MONGODB_URL` and that MongoDB is reachable
- Pinecone errors: ensure `PINECONE_API_KEY` and index exist
- Whisper transcription issues: verify `OPENAI_API_KEY` and ffmpeg availability if needed
- AKS issues: see [docs/DEPLOYMENT_AKS.md](./docs/DEPLOYMENT_AKS.md#troubleshooting)

## License
Proprietary or TBD.
