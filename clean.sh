#!/bin/bash

# Skip failing tests
SKIP=black,reorder-python-imports,double-quote-string-fixer poetry run pre-commit run --all-files

# Update hooks to latest
poetry run pre-commit autoupdate

# Run on all files
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
poetry lock; poetry check --lock --strict

# Only poetry.lock file dependencies are present
poetry sync

# But before you can publish your library, you will need to package it using the build command:
poetry build

# Packaging a project before publishing it is important because it makes the project easier to distribute, install, and use for others.
# Next, you have to configure your PyPI credentials properly as Poetry will publish the library to PyPI by default.

# Once you have packaged your library, you can publish it using the publish command:
poetry publish

# Export dependencies to requirements file
poetry export --output requirements.txt

# Install with dev and test but remove test, so just dev group
poetry install --with dev,test --without test



poetry config repositories.testpypi https://test.pypi.org/legacy/

poetry config http-basic.pypi scAB1001 ~Q~a]jhL]6$]8Kf

poetry config pypi-token.testpypi pypi-AgENdGVzdC5weXBpLm9yZwIkNGM2YzI4MDctN2E0Ny00NDFiLTliNDMtMTk5NGZlN2Y4N2RhAAIqWzMsImY2OTAxOTI1LTMxNDAtNDRjNy1hNDE2LTljZjhmYTJkYjk4OSJdAAAGINksoYhljcMM7iEjIOIeR1vWx9NAFjgQV8vcP-Wc6uA8

export POETRY_PYPI_TOKEN_TEST_PYPI=pypi-AgENdGVzdC5weXBpLm9yZwIkNGM2YzI4MDctN2E0Ny00NDFiLTliNDMtMTk5NGZlN2Y4N2RhAAIqWzMsImY2OTAxOTI1LTMxNDAtNDRjNy1hNDE2LTljZjhmYTJkYjk4OSJdAAAGINksoYhljcMM7iEjIOIeR1vWx9NAFjgQV8vcP-Wc6uA8
export POETRY_HTTP_BASIC_TEST_PYPI_USERNAME=scAB1001
export POETRY_HTTP_BASIC_TEST_PYPI_PASSWORD=~Q~a]jhL]6$]8Kf

poetry run twine upload --repository testpypi dist/* --verbose
poetry run twine upload --repository testpypi dist/* --username __token__ --password pypi-AgENdGVzdC5weXBpLm9yZwIkNGM2YzI4MDctN2E0Ny00NDFiLTliNDMtMTk5NGZlN2Y4N2RhAAIqWzMsImY2OTAxOTI1LTMxNDAtNDRjNy1hNDE2LTljZjhmYTJkYjk4OSJdAAAGINksoYhljcMM7iEjIOIeR1vWx9NAFjgQV8vcP-Wc6uA8


poetry add fastapi httpx pydantic pydantic-settings
poetry add python-dotenv black isort ruff mypy pre-commit twine --group dev
poetry add pytest pytest-cov pytest-asyncio --group test
poetry add uvicorn --group prod
poetry add sphinx --group docs
