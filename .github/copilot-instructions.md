# DoneFlow — Instruções para o GitHub Copilot

## Contexto do Projeto
Aplicação web de categorização automática de tarefas usando a Matriz de Eisenhower com IA.
O PRD completo está em `docs/PRD.md`. Leia-o antes de sugerir qualquer implementação.

## Stack Obrigatória
- Python 3.12 + FastAPI + Pydantic v2
- SQLAlchemy + SQLite (MVP)
- pytest + pytest-cov + httpx
- Anthropic Claude API (`claude-sonnet-4-20250514`)

## Metodologia: TDD ESTRITO
1. SEMPRE escreva o teste ANTES do código de produção
2. Ciclo obrigatório: Red → Green → Refactor
3. Cobertura mínima: 90% geral, 95% em unit tests
4. Nunca escreva código de produção sem teste correspondente

## Quadrantes da Matriz de Eisenhower
- `DO_NOW`: urgente + importante
- `SCHEDULE`: não urgente + importante
- `DELEGATE`: urgente + não importante
- `ELIMINATE`: não urgente + não importante

## Padrões de Código
- Type hints em TODAS as funções
- Docstrings em todos os métodos públicos
- PEP8 obrigatório
- Nomes de teste: `test_<comportamento>_<condicao>_<resultado_esperado>`