# Investment Portfolio API

REST API for investment portfolio management built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, and Docker.

## Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
- Pytest

## Architecture

The project follows a layered architecture with clear separation between:

- `api`: endpoints and routing
- `core`: settings and security
- `db`: engine, session, and declarative base
- `models`: ORM entities
- `schemas`: input and output contracts
- `services`: business rules
- `tests`: automated tests

## Running the Project

### Locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### With Docker

```bash
docker compose up --build
```

## Next Steps

- Configure application settings with `pydantic-settings`
- Implement JWT authentication
- Create the initial models and migrations
- Build auth, assets, and transactions endpoints
- Cover the main flows with automated tests
