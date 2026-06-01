# DoneFlow

[![CI](https://img.shields.io/github/actions/workflow/status/your-org/doneflow/ci.yml?branch=main&label=CI)](https://github.com/your-org/doneflow/actions/workflows/ci.yml)
[![Coverage](https://codecov.io/gh/your-org/doneflow/branch/main/graph/badge.svg)](https://codecov.io/gh/your-org/doneflow)
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

**DoneFlow** — categorização automática de tarefas com IA, FastAPI e Matriz de Eisenhower.

## Descrição do projeto

DoneFlow é uma API web para transformar uma descrição de tarefa em uma decisão prática de prioridade. O sistema recebe tarefas em linguagem natural, usa o Anthropic Claude (com fallback determinístico) para avaliar urgência e importância, e classifica cada item em um dos quatro quadrantes da Matriz de Eisenhower:

| Quadrante | Critério | Ação recomendada | Cor |
| --- | --- | --- | --- |
| `DO_NOW` | Urgente + importante | Fazer agora | Vermelho `#C0392B` |
| `SCHEDULE` | Não urgente + importante | Agendar | Azul `#2980B9` |
| `DELEGATE` | Urgente + não importante | Delegar | Amarelo `#E6A817` |
| `ELIMINATE` | Não urgente + não importante | Eliminar | Cinza `#555555` |

A aplicação segue arquitetura em camadas:

- **API:** FastAPI, OpenAPI, validação de entrada e rotas REST.
- **Serviços:** orquestração de tarefas e categorização por IA.
- **Repositórios:** acesso a dados com SQLAlchemy.
- **Configuração/Banco:** variáveis de ambiente, SQLite no MVP e suporte a URLs SQLAlchemy.

A documentação interativa fica disponível em `http://localhost:8000/docs` quando o servidor está em execução.

## Como rodar localmente

### Com Docker

Pré-requisitos:

- Docker
- Docker Compose
- Chave da Anthropic para categorização por IA (`ANTHROPIC_API_KEY`)

```bash
# Clone o repositório
git clone https://github.com/your-org/doneflow.git
cd doneflow

# Configure variáveis locais
cp .env.example .env
# Edite .env e defina ANTHROPIC_API_KEY

# Suba a API em http://localhost:8000
docker compose up --build
```

Comandos úteis:

```bash
# Rodar em segundo plano
docker compose up --build -d

# Ver logs
docker compose logs -f app

# Parar a aplicação
docker compose down

# Parar e remover o volume SQLite local
docker compose down -v
```

### Sem Docker

Pré-requisitos:

- Python 3.12+
- `pip`
- Chave da Anthropic para categorização por IA (`ANTHROPIC_API_KEY`)

```bash
# Clone o repositório
git clone https://github.com/your-org/doneflow.git
cd doneflow

# Crie e ative um ambiente virtual
python -m venv .venv
source .venv/bin/activate

# Instale a aplicação e dependências de desenvolvimento
pip install -e ".[dev]"

# Configure variáveis locais
cp .env.example .env
# Edite .env e defina ANTHROPIC_API_KEY

# Rode a API em http://localhost:8000
uvicorn doneflow.main:app --reload
```

> Observação: o `Dockerfile` usa `src.doneflow.api.main:app` por compatibilidade com o módulo histórico da API. Para desenvolvimento local instalado com `pip install -e`, `doneflow.main:app` é o ponto de entrada principal.

## Como rodar os testes

```bash
# Suite completa com cobertura mínima configurada no pyproject.toml
pytest

# Testes unitários
pytest tests/unit/ -v

# Testes de integração
pytest tests/integration/ -v

# Testes end-to-end
pytest tests/e2e/ -v

# Relatório HTML de cobertura em htmlcov/index.html
pytest --cov=src/doneflow --cov-report=html
```

Qualidade de código:

```bash
# Formatação
black src/ tests/

# Lint
ruff check src/ tests/

# Tipagem estática
mypy src/
```

## Estrutura de pastas

```text
doneflow/
├── .github/
│   └── workflows/            # Pipeline de CI
├── docs/
│   └── PRD.md                # Requisitos de produto
├── src/
│   └── doneflow/
│       ├── api/              # Rotas FastAPI e aplicação de compatibilidade
│       ├── models/           # Modelos SQLAlchemy e enums de domínio
│       ├── repositories/     # Camada de acesso a dados
│       ├── schemas/          # Schemas Pydantic de request/response
│       ├── services/         # Regras de negócio e integração com IA
│       ├── static/           # Frontend estático do MVP
│       ├── config.py         # Configurações via ambiente
│       ├── database.py       # Engine, sessão e inicialização do banco
│       └── main.py           # Aplicação FastAPI principal
├── tests/
│   ├── unit/                 # Testes isolados com mocks
│   ├── integration/          # Testes com FastAPI/TestClient e SQLite
│   └── e2e/                  # Fluxos ponta a ponta
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

## Endpoints principais

| Método | Endpoint | Descrição |
| --- | --- | --- |
| `POST` | `/api/v1/tasks` | Cria uma tarefa e classifica com IA |
| `GET` | `/api/v1/tasks` | Lista tarefas cadastradas |
| `GET` | `/api/v1/tasks/{task_id}` | Busca uma tarefa por UUID |
| `PATCH` | `/api/v1/tasks/{task_id}` | Atualiza manualmente descrição e/ou quadrante |
| `DELETE` | `/api/v1/tasks/{task_id}` | Remove uma tarefa |
| `GET` | `/api/v1/tasks/distribution` | Retorna estatísticas por quadrante |
| `GET` | `/health` | Verifica saúde da API e do banco |

## Documentação

- [Product Requirements Document (PRD)](docs/PRD.md)
- [OpenAPI local](http://localhost:8000/docs)

## Variáveis de ambiente

| Variável | Exemplo | Descrição |
| --- | --- | --- |
| `ANTHROPIC_API_KEY` | `sk-ant-...` | Chave usada pelo serviço de categorização por IA |
| `DATABASE_URL` | `sqlite:///doneflow.db` | URL SQLAlchemy do banco de dados |
| `LOG_LEVEL` | `INFO` | Nível de logs da aplicação |
| `AI_TIMEOUT_SECONDS` | `2` | Timeout da chamada de IA antes do fallback |
| `AI_CACHE_TTL_SECONDS` | `300` | TTL do cache de categorizações |

## Desenvolvimento

O projeto segue TDD estrito: escreva o teste primeiro, implemente o mínimo para passar e refatore mantendo a suíte verde. Antes de abrir um PR, rode testes, formatação, lint e type check.

## Licença

MIT. Consulte o arquivo [LICENSE](LICENSE) quando disponível no repositório.
