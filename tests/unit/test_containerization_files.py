from pathlib import Path


def test_dockerfile_multistage_python312_slim_and_non_root_runtime() -> None:
    dockerfile = Path("Dockerfile")
    assert dockerfile.exists()

    content = dockerfile.read_text(encoding="utf-8")

    assert "FROM python:3.12-slim AS builder" in content
    assert "FROM python:3.12-slim AS runtime" in content
    assert "USER appuser" in content
    assert "EXPOSE 8000" in content
    assert "UVICORN_WORKERS" in content


def test_docker_compose_has_app_service_and_sqlite_volume() -> None:
    compose_file = Path("docker-compose.yml")
    assert compose_file.exists()

    content = compose_file.read_text(encoding="utf-8")

    assert "services:" in content
    assert "app:" in content
    assert "volumes:" in content
    assert "ANTHROPIC_API_KEY" in content
    assert "sqlite_data:" in content
