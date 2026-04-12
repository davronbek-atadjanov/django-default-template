# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

DjangoDefault is a production-ready Django 5.2 boilerplate with DRF, JWT auth, PostgreSQL, Redis, Celery, and modern admin (Unfold). Uses `uv` as the package manager and `task` (go-task) for automation.

## Commands

All task commands use `uv run` as the default runner.

```bash
# Setup
uv sync                          # Install all dependency groups
cp .env.example .env             # Create env config (required)

# Development
uv run python src/manage.py runserver 0.0.0.0:8000
uv run python src/manage.py migrate
uv run python src/manage.py createsuperuser
uv run python src/manage.py secret_key   # Generate a new SECRET_KEY
uv run python src/manage.py makeapp <name>  # Scaffold a new app

# Code quality (via Taskfile.yml)
task format          # Auto-format with ruff (alias: task fmt)
task lint            # Lint check with ruff
task typecheck       # mypy strict type checking
task deptry          # Check for unused/missing dependencies
task all             # Full CI: format → deptry → typecheck → testcov → pre-commit

# Testing
task test            # Starts postgres-test container, runs pytest -vv
task testcov         # test + coverage report
uv run pytest -vv    # Run tests directly (needs test DB running)

# Docker
docker compose up -d --build
```

## Architecture

- **`src/core/`** — Django project root: settings, urls, wsgi/asgi, celery
  - **`config/`** — Modular settings split into: `rest_framework.py`, `jwt.py`, `cache.py`, `logs.py`, `sentry.py`, `swagger.py`, `ckeditor5.py`, `unfold.py`, `unfold_navigation.py`, `apps.py`
- **`src/apps/`** — Django applications
  - **`shared/`** — Base classes and utilities used by all apps: `AbstractBaseModel` (timestamped base model), custom pagination, JSON encoder, exception handler, Prometheus middleware
  - **`users/`** — Custom User model with email-based auth and role system (ADMIN, USER, MODERATOR)
- **`assets/`** — Static files, media uploads, locale translations, logs, templates
- **`deployments/compose/backend/`** — Dockerfile (multi-stage with uv), entrypoint/start scripts, celery scripts

### Key patterns

- **API versioning**: Apps use `api/v1/` subdirectories for views, serializers, and tests
- **Custom User model**: Email is the USERNAME_FIELD; uses custom `UserManager`
- **Exception handling**: All DRF exceptions go through `shared/exceptions/global.py` → standardized `{success, message, data}` response format
- **Pagination**: `CustomPagination` in `shared/utils/pagination.py` returns `{success, message, meta, links, data}` with page metadata
- **New apps**: Use `python src/manage.py makeapp <name>` to scaffold with the correct modular structure (models/, admin/, api/v1/)
- **i18n**: Three languages (uz, ru, en) with django-modeltranslation for model field translations

## Code Style

- **Ruff** for linting and formatting (line length 120, target Python 3.11)
- **mypy** in strict mode with django-stubs plugin
- Migrations are excluded from linting
- Pre-commit hooks enforce format, lint, and typecheck on every commit

## Configuration

- All secrets and service configs via `.env` (see `.env.example`)
- `DJANGO_SETTINGS_MODULE=core.settings` — PYTHONPATH must include `src/`
- PostgreSQL required; Redis for cache/sessions/Celery broker
- Sentry integration activates only when `SENTRY_DSN` is set
