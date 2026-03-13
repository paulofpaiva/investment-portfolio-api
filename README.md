# Investment Portfolio API

API REST para gerenciamento de carteira de investimentos construída com FastAPI, PostgreSQL, SQLAlchemy, Alembic e Docker.

## Stack

- Python
- FastAPI
- PostgreSQL
- SQLAlchemy
- Alembic
- Docker
- Pytest

## Estrutura

O projeto segue uma arquitetura em camadas com separação entre:

- `api`: endpoints e roteamento
- `core`: configurações e segurança
- `db`: engine, sessão e base declarativa
- `models`: entidades ORM
- `schemas`: contratos de entrada e saída
- `services`: regras de negócio
- `tests`: testes automatizados

## Como executar

### Localmente

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Com Docker

```bash
docker compose up --build
```

## Próximos passos

- Configurar settings com `pydantic-settings`
- Implementar autenticação JWT
- Criar models e migrations iniciais
- Desenvolver endpoints de auth, assets e transactions
- Cobrir fluxos com testes automatizados
