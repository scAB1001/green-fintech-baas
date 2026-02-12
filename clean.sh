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
