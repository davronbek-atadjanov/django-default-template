# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

cargo_backend — a production-ready Django 5.2 backend built on the DjangoDefault boilerplate. Stack: DRF + SimpleJWT, PostgreSQL, Redis, Celery, Unfold admin, Prometheus, Sentry. Uses `uv` for package management and `task` (go-task) for automation.

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
task test                              # Starts postgres-test container, runs pytest -vv
task testcov                           # test + coverage report
uv run pytest -vv                      # Run tests directly (needs test DB running)
uv run pytest tests/path/test_foo.py -vv           # Single test file
uv run pytest tests/path/test_foo.py::test_bar -vv # Single test function

# Docker
docker compose up -d --build
```

## Architecture

- **`src/core/`** — Django project root: settings, urls, wsgi/asgi, celery
  - **`config/`** — Modular settings. Each file exports via wildcard import in `config/__init__.py`, which `settings.py` imports with `from core.config import *`. Modules: `apps.py`, `rest_framework.py`, `jwt.py`, `cache.py`, `logs.py`, `sentry.py`, `swagger.py`, `unfold.py`, `unfold_navigation.py` (ckeditor5 currently commented out)
- **`src/apps/`** — Django applications
  - **`shared/`** — Base classes and utilities used by all apps: `AbstractBaseModel` (timestamped base model), custom pagination, JSON encoder, exception handler, Prometheus middleware, custom HTTP error handlers (404/500/403/400 returning JSON)
  - **`users/`** — Custom User model with email-based auth and role system (ADMIN, USER, MODERATOR)
- **`assets/`** — Static files, media uploads, locale translations, logs, templates
- **`deployments/compose/backend/`** — Dockerfile (multi-stage with uv), entrypoint/start scripts, celery scripts

### Key patterns

- **API versioning**: Apps use `api/v1/` with audience-based splits: `api/v1/admin/`, `api/v1/client/`, `api/v1/wms/`. Each split has its own `views/`, `serializers/`, and `urls.py`
- **Custom User model**: Email is the USERNAME_FIELD; uses custom `UserManager`; has `tokens()` method returning JWT access/refresh pair
- **Exception handling**: All DRF exceptions go through `shared/exceptions/global.py` → standardized `{success, message, data}` response format
- **Pagination**: `CustomPagination` (page_size=20, max=100) returns `{success, message, meta, links, data}` with page metadata
- **New apps**: Use `python src/manage.py makeapp <name>` to scaffold with the correct modular structure (models/, admin/, api/v1/)
- **i18n**: Three languages (uz, ru, en) with django-modeltranslation for model field translations
- **Swagger docs**: Every view must use `@extend_schema` with explicit request/response serializers and `OpenApiExample`. Response serializers must reflect the `{success, message, data}` wrapper format. Request examples must match the actual payload. Swagger UI requires admin login — available at `/api/schema/swagger-ui/`, ReDoc at `/api/schema/redoc/`
- **DRF defaults**: JWT auth required, JSON renderer only, scoped throttling (anon: 60/min, user: 1000/day). Custom exception handler and pagination are set globally in `core/config/rest_framework.py`
- **URL routing**: `core/urls.py` wraps admin in `i18n_patterns`. App URLs included from `apps.shared.urls`. Swagger patterns appended from `core/config/swagger.py`

## Code Style

- **Ruff** for linting and formatting (line length 120, target Python 3.11)
- **mypy** in strict mode with django-stubs plugin (`core/settings.py` excluded from mypy)
- Migrations are excluded from linting; `S101` (assert) allowed in tests
- Pre-commit hooks run `task format`, `task lint`, and `task typecheck` on every commit (tests are commented out in `.pre-commit-config.yaml`)

## Configuration

- All secrets and service configs via `.env` (see `.env.example`)
- `DJANGO_SETTINGS_MODULE=core.settings` — PYTHONPATH must include `src/`
- pytest also uses `DJANGO_SETTINGS_MODULE=core.settings` with `testpaths = ["tests"]`
- PostgreSQL required; Redis for cache/sessions/Celery broker
- Sentry integration activates only when `SENTRY_DSN` is set
- Custom CSRF: header `X_SESSION_TOKEN`, field name `session_token`, session cookie named `sid`
