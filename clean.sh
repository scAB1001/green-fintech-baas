#!/bin/bash


###                 ###
###  Poetry         ###
###                 ###
# Add dependencies to pyproject.toml
poetry add fastapi httpx pydantic pydantic-settings
poetry add python-dotenv black isort ruff mypy pre-commit twine --group dev
poetry add pytest pytest-cov pytest-asyncio --group test
poetry add uvicorn --group prod
poetry add sphinx --group docs

# Update hooks to latest
poetry run pre-commit autoupdate

# Run on all files
# SKIP=black
poetry run pre-commit run --all-files --verbose

# Fix individually
poetry run black src/ tests/

# If ruff fails:
poetry run ruff check --fix src/ tests/

# Show unsafe fixes
poetry run ruff check --unsafe-fixes

# Ruff enforcing F401, and no other rules
poetry run ruff check --select F401

# Verify structure of lock file and require no warnings or errors
poetry lock --regenerate; poetry check --lock --strict

# Only poetry.lock file dependencies are present
poetry sync

# But before you can publish your library, you will need to package it using the build command:
poetry build

# Package the project before publishing.
# Configure your PyPI credentials properly to publish to PyPI.
poetry publish

# Export dependencies to requirements file
poetry export --output requirements.txt

# Install with dev and test but remove test, so just dev group
poetry install --with dev,test,prod,docs --without test


###                 ###
###  PyPI           ###
###                 ###
poetry config repositories.testpypi https://test.pypi.org/legacy/
poetry config http-basic.pypi <user> <pass>
poetry config pypi-token.testpypi <token>

poetry run twine upload --repository testpypi dist/* --verbose
poetry run twine upload --repository testpypi dist/* --username __token__ --password <token>


###                 ###
###  Test           ###
###                 ###
# Testing FastAPI Python App
poetry run pytest -v
poetry run uvicorn app.main:app --reload
# Go to /docs to see auto-generated API docs
# Go to /


###                 ###
###  DOCKER         ###
###                 ###
# Stop and remove everything from this project
docker compose down --remove-orphans -v

# Verify no containers remain
docker ps -a | grep green-fintech

# Start PostgreSQL only (no app container)
docker compose up -d postgres

# Use pgpass Feature Branch 1.4: PostgreSQL with Docker

# Start PostgreSQL (automatically creates .pgpass)
./scripts/db-helper.sh start

# Show configuration (now works with .pgpass)
./scripts/db-helper.sh config

# Check connections
./scripts/db-helper.sh connections

# View database stats
./scripts/db-helper.sh stats

# See table sizes
./scripts/db-helper.sh tables

# Run custom query
./scripts/db-helper.sh sql "SELECT 'Hello' as greeting;"

# Test all access methods
./scripts/db-helper.sh test-access

# When done, .pgpass is automatically cleaned up
./scripts/db-helper.sh stop
