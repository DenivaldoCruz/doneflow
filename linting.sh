#!/bin/bash

echo "Formating code with Black"
black src/ tests/

echo "Linting with Ruff"
ruff check src/ tests/ --fix

echo "Type checking with mypy"
mypy src/