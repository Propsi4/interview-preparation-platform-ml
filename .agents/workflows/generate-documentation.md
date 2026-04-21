---
description: "Autonomous Repository Documentation Generator — ML Service"
---

This workflow guides an agent to autonomously create a comprehensive, professional-grade documentation suite for the **Interview Preparation Platform ML Service** repository using specialized AI skills.

# Objective
Transform the ML service repository into a well-documented product with onboarding guides, architectural deep-dives, agent documentation, API references, and technical walkthroughs stored in the `docs/` folder.

# Prerequisites
The agent must have access to the following skills:
- `wiki-architect`
- `wiki-page-writer`
- `backend-architect`
- `api-patterns`
- `pydantic-models-py`
- `documentation`

# Steps

## 1. Planning & Catalogue Generation
- Call the `wiki-architect` skill.
- **Action**: Scan the entire repository structure, identifying key modules: `src/agents/`, `src/api/`, `src/scrapers/`, `src/jobs/`, `src/db/`, `src/services/`, `src/config/`, `src/conversation_history/`, and `src/tools/`.
- **Output**: Generate a hierarchical JSON catalogue of documentation pages following this target structure:
  ```
  docs/
  ├── onboarding.md
  ├── architecture_overview.md
  ├── agents/
  │   ├── agent_system.md
  │   ├── interview_agent.md
  │   └── assessment_agent.md
  ├── api/
  │   ├── rest_endpoints.md
  │   ├── websocket_speech.md
  │   └── schemas.md
  ├── scrapers/
  │   └── vacancy_scraper.md
  ├── jobs/
  │   └── celery_tasks.md
  ├── database/
  │   └── data_model.md
  └── configuration.md
  ```
- **Organization**: Ensure the `docs/` directory and all subdirectories exist.

## 2. Onboarding & High-Level Architecture
- Call the `wiki-page-writer` skill for the "Onboarding" section.
- **Requirement**: Use the "Principal-Level Guide" and "Zero-to-Hero" patterns.
- **Action**: Create `docs/onboarding.md`:
  - Poetry-based environment setup instructions.
  - How to run the FastAPI server (`scripts/run_api.sh`), Celery worker (`scripts/run_celery.sh`), and required services (PostgreSQL, Redis).
  - Environment variable reference (`.env` / `example.env`).
  - First-run checklist: database migration with Alembic, seeding data, verifying health.
- **Action**: Create `docs/architecture_overview.md`:
  - System context diagram showing: Frontend ↔ ML API ↔ PostgreSQL/Redis/OpenAI.
  - Container diagram: FastAPI server, Celery workers, Playwright scrapers, AI agent pipeline.
  - Data flow: from vacancy search → scraping → requirements extraction → interview → assessment.
- **Constraint**: Each file must include at least 2 dark-mode Mermaid diagrams.

## 3. Agent System Deep-Dive
- For the `src/agents/` module:
  - Use `wiki-page-writer` to TRACE ACTUAL CODE PATHS in `src/agents/implementations/`.
  - Call `backend-architect` to refine the agent orchestration design.
  - Create `docs/agents/agent_system.md`:
    - Overall agent architecture: base classes, DSPy modules, LangChain integration.
    - How agents are registered and invoked.
    - Conversation history management (`src/conversation_history/`).
  - Create `docs/agents/interview_agent.md`:
    - The `interview` agent implementation: prompt design, multi-turn conversation flow, WebSocket streaming integration.
    - How user responses are processed and follow-up questions are generated.
  - Create `docs/agents/assessment_agent.md`:
    - The `assessment` agent: how interview transcripts are scored.
    - Requirements extraction and aggregation pipeline (`requirements_extractor`, `requirements_aggregator`).
    - The `chat_summarizer` agent role in the pipeline.
- **Constraint**: Every claim MUST have a source citation `(file_path:line_number)`.

## 4. API & Technical Reference
- Call the `api-patterns` skill.
- **Action**: Review `src/api/routes/` and document all endpoints:
  - `chat.py` — Chat session management.
  - `chat_history.py` — Conversation history retrieval.
  - `evaluation.py` — Interview evaluation triggers.
  - `scrapers.py` — Vacancy scraping triggers.
  - `speech.py` — WebSocket-based STT/TTS streaming.
- **Output**: Create `docs/api/rest_endpoints.md` covering all HTTP endpoints with method, path, request/response schemas, and example payloads.
- **Output**: Create `docs/api/websocket_speech.md` documenting the WebSocket protocol:
  - Connection lifecycle, message types (`start`, `audio`, `end`), response events (`transcript`, `answer`, `audio_chunk`, `complete`).
  - Sequence diagram of a full speech-to-speech session.
- Call the `pydantic-models-py` skill.
- **Action**: Review `src/api/schemas.py` and `src/scrapers/schemas/`.
- **Output**: Create `docs/api/schemas.md` documenting all Pydantic request/response models with field descriptions, types, validators, and examples.

## 5. Scraper Documentation
- Use `wiki-page-writer` to TRACE ACTUAL CODE PATHS in `src/scrapers/`.
- Call `backend-architect` to explain the scraper pipeline architecture.
- **Output**: Create `docs/scrapers/vacancy_scraper.md`:
  - DOU vacancy scraper (`src/scrapers/implementations/dou.py`): Playwright browser automation flow.
  - Scraper base class and pipeline pattern (`src/scrapers/base.py`, `src/scrapers/pipelines/`).
  - Data flow: raw HTML → parsed vacancy → database storage.
- **Constraint**: Every claim MUST have a source citation `(file_path:line_number)`.

## 6. Background Jobs Documentation
- Use `wiki-page-writer` to document the Celery task system.
- Call `backend-architect` to explain the distributed task architecture.
- **Output**: Create `docs/jobs/celery_tasks.md`:
  - Celery configuration (`src/jobs/celery_app.py`).
  - All registered tasks in `src/jobs/tasks/`:
    - `scrape_dou_vacancies_overview.py` — Bulk vacancy discovery.
    - `scrape_dou_vacancy_details.py` — Individual vacancy detail enrichment.
    - `unify_requirements.py` — Requirements aggregation across vacancies.
    - `evaluate_vacancy_interview.py` — Post-interview scoring.
  - Job pipelines in `src/jobs/pipelines/`.
  - Task orchestration: chaining, error handling, retry policies.
- **Constraint**: Include a Mermaid sequence or flowchart diagram showing the task pipeline.

## 7. Database & Data Model Documentation
- Use `wiki-page-writer` to document the data layer.
- **Output**: Create `docs/database/data_model.md`:
  - SQLAlchemy models in `src/db/models/`: `vacancies`, `chat_session`, `chat_message`, `search_query`, `unified_requirements`, `vacancy_interview_score`.
  - Repository pattern in `src/db/repositories/`: base repository, per-entity repositories.
  - Database engine configuration (`src/db/engine.py`).
  - Alembic migrations overview (`src/db/migrations/`).
  - Entity-relationship diagram as a Mermaid ER diagram.

## 8. Configuration Reference
- Use `wiki-page-writer` to create `docs/configuration.md`:
  - All Pydantic Settings classes in `src/config/`: `api.py`, `app.py`, `db.py`, `openai.py`, `redis.py`.
  - Environment variable table: variable name, type, default, description.
  - How settings are loaded and validated at startup.
  - Docker configuration (`Dockerfile`) and deployment notes.

## 9. Main Entry Point (README)
- Call the `documentation` skill.
- **Action**: Update the root `README.md`.
- **Action**: Add a "Technical Documentation" section linking to every file in `docs/`.
- **Action**: Ensure a professional structure:
  1. Overview & Purpose
  2. Tech Stack (Python 3.13, FastAPI, DSPy, LangChain, Celery, SQLAlchemy, Playwright, OpenAI)
  3. Quick Start (link to `docs/onboarding.md`)
  4. Architecture (link to `docs/architecture_overview.md`)
  5. Documentation Index (links to all `docs/` pages)
  6. Development (pre-commit, linting, testing)
  7. Contributing

## 10. Final Audit
- Verify all internal links between documentation files are valid.
- Ensure Mermaid syntax is correct for dark mode as per `wiki-page-writer` constraints.
- Confirm every primary feature (agents, API, scrapers, jobs, database) has a corresponding deep-dive in `docs/`.
- Verify that all source citations `(file_path:line_number)` point to existing code.
- Check the `README.md` documentation index links resolve correctly.
