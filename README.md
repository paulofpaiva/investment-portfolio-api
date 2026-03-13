# Investment Portfolio API

REST API for investment portfolio management built with FastAPI, PostgreSQL, SQLAlchemy, Alembic, and Docker.

## Tech Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker

## Build and Run

### Docker

```bash
docker compose up --build
```

API: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`

### Local CLI

1. Start only the database:

```bash
docker compose up -d db
```

2. Create a local environment file:

```bash
cp .env.example .env
```

3. Update `DATABASE_URL` in `.env` to use `localhost`:

```env
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/investment_portfolio
```

4. Install dependencies and run the API:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

API: `http://localhost:8000`  
Docs: `http://localhost:8000/docs`
