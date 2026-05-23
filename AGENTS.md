# AGENTS.md — Guidance for AI Coding Agents

## Project Overview

**DoneFlow** is an AI-powered task categorization system using the Eisenhower Matrix. The MVP uses Python 3.12 + FastAPI + Pydantic v2, with Anthropic Claude API for intelligent task classification into four quadrants: `DO_NOW`, `SCHEDULE`, `DELEGATE`, `ELIMINATE`.

**Key Constraint:** Strict TDD methodology — **ALWAYS write tests before production code**. Test coverage minimum: 90% overall, 95% for unit tests.

---

## Architecture & Component Boundaries

### Layered Architecture (4 Tiers)

1. **API Layer** (`src/doneflow/api/`)
   - FastAPI endpoints at `/api/v1/`
   - Request/response validation via Pydantic schemas
   - Health checks and OpenAPI documentation

2. **Service Layer** (`src/doneflow/services/`)
   - `TaskService`: Task CRUD and orchestration
   - `AICategorizationService`: Anthropic Claude integration (categorize tasks)
   - Business logic isolated from HTTP concerns

3. **Data Layer** (`src/doneflow/repositories/`)
   - SQLAlchemy ORM models in `models/`
   - Repository pattern for database access
   - SQLite for MVP, PostgreSQL for production

4. **Configuration & Database**
   - Environment variables via `pydantic-settings`
   - Connection pooling via SQLAlchemy
   - Database initialization in startup hooks

### Data Flow for Task Categorization

```
POST /api/v1/tasks {description}
  ↓
TaskService.create_and_categorize()
  ↓
AICategorizationService.classify_task()
  ↓
Anthropic Claude API (structured prompt)
  ↓
Returns: {quadrant: Quadrant enum, confidence: float}
  ↓
TaskRepository.save()
  ↓
200 + {id, description, quadrant, created_at}
```

---

## Eisenhower Matrix Quadrants (Enums)

**Critical:** Must be exact enum names in code:

- `DO_NOW` → Urgent + Important (Red `#C0392B`)
- `SCHEDULE` → ¬Urgent + Important (Blue `#2980B9`)
- `DELEGATE` → Urgent + ¬Important (Yellow `#E6A817`)
- `ELIMINATE` → ¬Urgent + ¬Important (Gray `#555555`)

Refer to these in Pydantic schemas, SQLAlchemy models, and AI prompt templates.

---

## TDD Workflow & Test Organization

### Mandatory Cycle: Red → Green → Refactor

1. **RED:** Write test in `tests/unit/` or `tests/integration/` that **fails**
2. **GREEN:** Write minimal production code to pass test
3. **REFACTOR:** Improve code while keeping test green

**Never** write production code without a corresponding test.

### Test Structure

```
tests/
├── unit/                    # Isolated, mock external dependencies
│   ├── test_models.py       # ORM model validation
│   ├── test_services.py     # Business logic with mocks
│   └── test_schemas.py      # Pydantic validation
├── integration/             # With real DB (SQLite in-memory)
│   └── test_api_endpoints.py # FastAPI TestClient
└── conftest.py              # Shared fixtures (pytest config)
```

### Naming Convention for Tests

```python
def test_<behavior>_<condition>_<expected_result>():
    """Example: test_task_with_urgent_keyword_classified_as_do_now"""
```

### Key Fixtures in `conftest.py`

- Setup SQLite in-memory database for integration tests
- Create FastAPI TestClient
- Mock Anthropic API responses
- Provide factory functions for test data

### Coverage Requirements

- Run: `pytest --cov=src/doneflow --cov-report=html`
- Minimum: 90% overall, 95% unit tests
- Exclude: `__repr__`, `__init__` boilerplate, `if TYPE_CHECKING`, abstract methods

---

## AI Integration: Anthropic Claude API

### Service: `AICategorizationService`

**Location:** `src/doneflow/services/` (to be implemented)

**Interface:**
```python
def classify_task(task_description: str) -> dict[str, Any]:
    """
    Classify task into quadrant using Claude API.
    
    Returns: {"quadrant": Quadrant, "confidence": float}
    """
```

### Prompt Engineering Pattern

Use **structured prompts** with:
- Task description input
- Clear urgency/importance evaluation criteria
- Keywords from PRD (urgency: "hoje", "urgente", "deadline", etc.)
- JSON-structured output for reliable parsing

### Fallback & Error Handling

- Timeout: If API exceeds 2 seconds, use deterministic fallback
- Fallback: Simple keyword-matching classifier (urgency/importance heuristics)
- Logging: Always log API calls and response times for monitoring

### Mocking for Tests

Mock Claude API in unit tests; use `unittest.mock.patch` or `pytest-mock`. In integration tests with real DB, either:
- Use `responses` library for HTTP mocking
- Create fixture that returns canned Claude responses

---

## Code Standards (Mandatory)

### Type Hints
- **ALL** function signatures require type hints
- Use `from typing import` for complex types (Union, Optional, etc.)
- Pydantic models self-document via class attributes

```python
def create_task(description: str, user_id: int) -> Task:
    """Docstring here."""
```

### Docstrings
- Required for all public methods and classes
- Use Google-style format
- Include parameter descriptions and return type

```python
def classify_task(description: str) -> dict[str, Any]:
    """Classify task using Anthropic Claude API.
    
    Args:
        description: Task text to classify
        
    Returns:
        Dictionary with 'quadrant' (Quadrant enum) and 'confidence' (float)
        
    Raises:
        TimeoutError: If API exceeds threshold
    """
```

### PEP 8 & Formatting

- Line length: 100 chars (via Black config in `pyproject.toml`)
- Use `black` for formatting: `black src/ tests/`
- Lint with `ruff`: `ruff check src/ tests/`
- Type check with `mypy`: `mypy src/` (strict mode enabled)

### Imports

- Standard library first, then third-party, then local
- One import per line for clarity (not `import a, b, c`)
- Use `from module import specific_class` to reduce namespace pollution

---

## Development Workflow & Commands

### Setup Environment

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Running the Application

```bash
# Start FastAPI server (localhost:8000)
uvicorn src.doneflow.api.main:app --reload

# API docs: http://localhost:8000/docs (Swagger UI)
# OpenAPI schema: http://localhost:8000/openapi.json
```

### Testing

```bash
# Run all tests with coverage
pytest

# Only unit tests (fast, should be 95%+ of test suite)
pytest tests/unit/ -v

# Only integration tests (slower, but essential)
pytest tests/integration/ -v

# Generate HTML coverage report
pytest --cov=src/doneflow --cov-report=html
# Open htmlcov/index.html in browser
```

### Code Quality

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/ --fix

# Type check
mypy src/
```

---

## API Endpoints Specification

All endpoints return JSON with standard status codes.

| Method | Endpoint | Behavior | Status |
|--------|----------|----------|--------|
| `POST` | `/api/v1/tasks` | Create + AI categorize | 201 created \| 422 validation |
| `GET` | `/api/v1/tasks` | List all tasks | 200 |
| `GET` | `/api/v1/tasks/{id}` | Get by ID | 200 \| 404 |
| `PATCH` | `/api/v1/tasks/{id}` | Manual recategorize | 200 \| 404 \| 422 |
| `DELETE` | `/api/v1/tasks/{id}` | Remove | 204 \| 404 |
| `GET` | `/api/v1/tasks/distribution` | Stats per quadrant | 200 |
| `GET` | `/health` | Health check | 200 |

### Request/Response Schemas (Pydantic)

- Define in `src/doneflow/api/schemas.py` (to be created)
- Use Pydantic v2 field validators, not property setters
- Return appropriate error responses (400 bad input, 404 not found, 500 server error)

---

## Project Files & Key Locations

| File | Purpose |
|------|---------|
| `docs/PRD.md` | **READ FIRST** — complete product requirements |
| `.github/copilot-instructions.md` | Quick reference for coding rules |
| `pyproject.toml` | Python dependencies, pytest config, black/ruff/mypy settings |
| `src/doneflow/models/` | SQLAlchemy ORM Task model |
| `src/doneflow/services/` | TaskService, AICategorizationService |
| `src/doneflow/repositories/` | TaskRepository (data access) |
| `src/doneflow/api/` | FastAPI app, routers, schemas |
| `tests/conftest.py` | Shared pytest fixtures |

---

## Common Patterns & Anti-Patterns

### ✅ DO

- **Mock external APIs** in unit tests (Anthropic, database)
- **Use fixtures** for database setup/teardown
- **Validate input** via Pydantic before processing
- **Return typed responses** from all functions
- **Log important operations** (task creation, API calls)
- **Test error paths** (timeouts, invalid input, empty results)

### ❌ DON'T

- **Skip tests** or claim "I'll test later"
- **Mix concerns** (API logic in models, DB access in services)
- **Use plain strings** for magic values (use enums for Quadrant)
- **Ignore type hints** or `mypy` errors
- **Write untested utility functions**
- **Commit code** with coverage < 90% or failing tests

---

## Integration Points & External Dependencies

### Anthropic Claude API

- **Model:** `claude-sonnet-4-20250514` (as per copilot-instructions.md)
- **Timeout:** Must respond in < 2 seconds (P95)
- **Auth:** Via `ANTHROPIC_API_KEY` environment variable
- **Rate limits:** Monitor token usage; implement backoff if needed

### SQLite (MVP) / PostgreSQL (Prod)

- **ORM:** SQLAlchemy v2
- **Migrations:** Alembic (if implemented; not in MVP)
- **Connection:** Via `DATABASE_URL` env var
- **Testing:** Use in-memory SQLite (`:memory:`) for speed

### Environment Variables

Set in `.env` or exported to shell:

```bash
ANTHROPIC_API_KEY=sk-...
DATABASE_URL=sqlite:///doneflow.db  # or postgres://...
DEBUG=true
LOG_LEVEL=INFO
```

---

## References & Reading Order

1. **Start:** `docs/PRD.md` (product vision, requirements, architecture)
2. **Quick rules:** `.github/copilot-instructions.md` (this project's TDD rules)
3. **Setup:** `README.md` (quick start, project structure)
4. **Code:** Read existing models, services, tests as patterns
5. **Tests:** `tests/conftest.py` and example test files for fixture patterns

---

## Summary for New Agents

**Before coding anything:**

1. ✅ Read `PRD.md` to understand product requirements
2. ✅ Check existing test patterns in `tests/`
3. ✅ Verify feature maps to one of four quadrants or core API endpoint
4. ✅ **Write test first** (TDD), then code, then refactor
5. ✅ Run `pytest --cov` to verify 90%+ coverage
6. ✅ Run `black`, `ruff`, `mypy` before committing

**Golden Rule:** If there's no test, there should be no production code.

