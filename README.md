# 🌱 Green FinTech BaaS Simulator API

[![.github/workflows/ci.yml](https://github.com/scAB1001/green-fintech-baas/actions/workflows/ci.yml/badge.svg?branch=develop)](https://github.com/scAB1001/green-fintech-baas/actions/workflows/ci.yml)

A sophisticated Banking-as-a-Service (BaaS) simulation platform for green financing and ESG analytics. Built with modern Python tooling and best practices.

## 🏗️ Architecture

- **API**: FastAPI (async, OpenAPI 3.1)
- **Database**: PostgreSQL 16+ with SQLAlchemy 2.0 (async)
- **Caching**: Redis (for score optimisation)
- **Containerisation**: Docker + Docker Compose
- **CI/CD**: GitHub Actions with conventional commits
- **Deployment**: Railway.app (production) / local with uv

## 📋 Prerequisites

- Python 3.12+
- Poetry
- Docker version 29.2.1, build a5c7197 & Docker Compose v5.0.2
- PostgreSQL 18+ (or Docker)
- Redis 7+ (optional, Stage 2)

## 🚀 Quick Start

```bash
# Clone repository SSH/HTTPS
git clone git@github.com:scAB1001/green-fintech-baas.git
git clone https://github.com/scAB1001/green-fintech-baas.git

# Navigate to project directory
cd green-fintech-baas

# Install dependencies
poetry install

# Copy environment template
cp .env.example .env

# Start services
docker-compose up -d

# Run migrations
poetry run alembic upgrade head

# Start development server
poetry run uvicorn src.app.main:app --reload
```

## 📚 Documentation

API documentation is automatically generated at /docs when running.

## 🧪 Testing

```bash
poetry run pytest
```

## 📦 Deployment

Deployed via Railway.app with GitHub Actions automation.

## 📄 License

Academic project - University of Leeds COMP3011 - MIT
