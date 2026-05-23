# DoneFlow

**Task Categorization with AI and Eisenhower Matrix**

[![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-green)](LICENSE)
[![Test Coverage](https://img.shields.io/badge/coverage-90%25%2B-brightgreen)](#testing)

DoneFlow is a web application that automatically categorizes user tasks using Artificial Intelligence and the Eisenhower Matrix framework. The system classifies tasks into four quadrants: **Do Now**, **Schedule**, **Delegate**, and **Eliminate**.

## Features

- 🤖 **AI-Powered Categorization** using Anthropic Claude API
- 📊 **Eisenhower Matrix** visualization with four quadrants
- ⚡ **Fast Processing** with response times < 2 seconds
- 🎨 **Dark-Mode UI** professional and intuitive interface
- ✅ **Test-Driven Development** with 90%+ code coverage
- 🔌 **RESTful API** for extensible integrations

## Quadrants

| Quadrant | Criteria | Action | Color |
|----------|----------|--------|-------|
| **Do Now** | Urgent + Important | Execute immediately | 🔴 Red |
| **Schedule** | Not Urgent + Important | Plan and program | 🔵 Blue |
| **Delegate** | Urgent + Not Important | Transfer to others | 🟡 Yellow |
| **Eliminate** | Not Urgent + Not Important | Discard or postpone | ⚫ Gray |

## Quick Start

### Prerequisites

- Python 3.12+
- pip or poetry
- Anthropic API key

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/doneflow.git
cd doneflow

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"

# Set up environment variables
cp .env.example .env
# Edit .env with your Anthropic API key
```

### Running the Application

```bash
# Run the FastAPI server
uvicorn src.doneflow.api.main:app --reload

# Access the API documentation
# Open http://localhost:8000/docs
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run only unit tests
pytest tests/unit/ -v

# Run only integration tests
pytest tests/integration/ -v

# Generate coverage report
pytest --cov=src/doneflow --cov-report=html
```

## Project Structure

```
doneflow/
├── .github/
│   └── copilot-instructions.md
├── docs/
│   └── PRD.md
├── src/
│   └── doneflow/
│       ├── __init__.py
│       ├── models/          # SQLAlchemy ORM models
│       ├── services/        # Business logic
│       ├── api/             # FastAPI endpoints
│       └── repositories/    # Data access layer
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── pyproject.toml
└── README.md
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/tasks` | Create task and categorize via AI |
| `GET` | `/api/v1/tasks` | List all tasks |
| `GET` | `/api/v1/tasks/{id}` | Get task by ID |
| `PATCH` | `/api/v1/tasks/{id}` | Reclassify task manually |
| `DELETE` | `/api/v1/tasks/{id}` | Remove task |
| `GET` | `/api/v1/tasks/distribution` | Get statistics by quadrant |
| `GET` | `/health` | Health check |

## Development

### Methodology: Test-Driven Development (TDD)

All features are developed following the **Red → Green → Refactor** cycle:

1. Write test first
2. Run test (RED - fails)
3. Write minimal code to pass test (GREEN)
4. Refactor code while maintaining tests (REFACTOR)

### Code Standards

- **Type Hints** in all functions
- **Docstrings** in all public methods
- **PEP 8** compliance
- **90%+ test coverage** minimum
- **95%+ unit test coverage** minimum

### Linting and Formatting

```bash
# Format code with Black
black src/ tests/

# Lint with Ruff
ruff check src/ tests/

# Type checking with mypy
mypy src/
```

## Documentation

- 📖 [Product Requirements Document (PRD)](docs/PRD.md)
- 📋 [Copilot Instructions](​.github/copilot-instructions.md)

## Technology Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12 + FastAPI |
| AI/NLP | Anthropic Claude API |
| Validation | Pydantic v2 |
| Database | SQLAlchemy + SQLite (MVP) / PostgreSQL (prod) |
| Testing | pytest + pytest-cov + httpx |
| Frontend | HTML5 + CSS3 + Vanilla JS (MVP) |

## Contributing

1. Follow the TDD methodology strictly
2. Maintain 90%+ test coverage
3. Write clear commit messages
4. Create meaningful pull requests

## License

MIT License - See LICENSE file for details

## Support

For issues, questions, or suggestions, please open an issue on GitHub.

---

**DoneFlow — Matriz de Eisenhower · IA**
*Categorização Automática de Tarefas com Python, FastAPI e TDD*

