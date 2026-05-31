"""Static documentation checks for DoneFlow public developer docs."""

from __future__ import annotations

from pathlib import Path


def test_readme_documents_required_project_sections() -> None:
    """README should explain CI, coverage, local execution, tests, structure, and PRD."""
    content = Path("README.md").read_text(encoding="utf-8")

    assert "github/actions/workflow/status" in content
    assert "codecov.io" in content
    assert "## Descrição do projeto" in content
    assert "## Como rodar localmente" in content
    assert "### Com Docker" in content
    assert "### Sem Docker" in content
    assert "## Como rodar os testes" in content
    assert "## Estrutura de pastas" in content
    assert "[Product Requirements Document (PRD)](docs/PRD.md)" in content


def test_readme_includes_docker_and_non_docker_commands() -> None:
    """README should provide copy-pasteable commands for Docker and Python workflows."""
    content = Path("README.md").read_text(encoding="utf-8")

    assert "docker compose up --build" in content
    assert 'pip install -e ".[dev]"' in content
    assert "uvicorn doneflow.main:app --reload" in content
    assert "pytest --cov=src/doneflow --cov-report=html" in content
