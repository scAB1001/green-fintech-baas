# Green FinTech BaaS (Banking-as-a-Service) API 🍃

[![Security Scan](https://github.com/scAB1001/green-fintech-baas/actions/workflows/security.yaml/badge.svg?branch=develop)](https://github.com/scAB1001/green-fintech-baas/actions/workflows/security.yaml)
[![Release](https://github.com/scAB1001/green-fintech-baas/actions/workflows/release.yaml/badge.svg?branch=main)](https://github.com/scAB1001/green-fintech-baas/actions/workflows/release.yaml)
[![CI](https://github.com/scAB1001/green-fintech-baas/actions/workflows/ci.yaml/badge.svg?branch=develop)](https://github.com/scAB1001/green-fintech-baas/actions/workflows/ci.yaml)
[![Dependabot Updates](https://github.com/scAB1001/green-fintech-baas/actions/workflows/dependabot/dependabot-updates/badge.svg?branch=main)](https://github.com/scAB1001/green-fintech-baas/actions/workflows/dependabot/dependabot-updates)

An elite, asynchronous REST API designed to bridge the gap between corporate financial data and environmental sustainability.

**The Problem:** Traditional lenders lack the specialized data models to accurately assess the financial risk of sustainability-focused projects, creating a "green financing gap."
**The Solution:** This platform acts as a BaaS backend, actively ingesting live corporate registry data from OpenCorporates, cross-referencing it against UK national energy and regional emissions datasets to gain ESG analytics, and dynamically generating Sustainability-Linked Loan (SLL) quotes.

## 📚 Academic Deliverables & Documentation

As per the COMP3011 coursework requirements, all formal academic justifications and comprehensive technical manuals are located within this repository:

* **📄 [Technical Report (PDF)](https://www.google.com/search?q=./Technical_Report.pdf):** Academic justification of the tech stack, architectural design choices, GenAI usage logs, and evaluation of limitations.
* **📄 [API Documentation (PDF)](https://www.google.com/search?q=./API_Documentation.pdf):** The formal OpenAPI specification, documenting all endpoints, parameters, request/response JSON payloads, and error codes.
* **📘 [Developer Wiki](https://www.google.com/search?q=https://github.com/scAB1001/green-fintech-baas/wiki):** The operational manual containing the Development Setup Guide, CI/CD Automation Guide, Testing Strategy, and Agile Project Management records.

---

## 🏗 Architecture & Tech Stack

This project strictly adheres to Domain-Driven Design (DDD) principles and features a robust separation of concerns between HTTP routing, business logic (Services), and database persistence (SQLAlchemy ORM).

* **Core Framework:** FastAPI (Asynchronous ASGI, OpenAPI 3.1)
* **Database:** PostgreSQL 18+ with SQLAlchemy 2.0 (asyncpg) and Alembic Migrations
* **Caching Tier:** Redis 8+ (In-memory caching with Base64 binary serialization)
* **Package Management:** `uv` (Deterministic, ultra-fast dependency resolution)
* **Media Generation:** ReportLab (Dynamic PDF) & Python Native `csv`
* **Testing:** Pytest with advanced `unittest.mock` patching (100% Branch Coverage)
* **DevOps:** Docker Compose, GitHub Actions (CI/CD), GHCR Immutable Artifacts

## ⚙️ Core Mathematical Engine

The API calculates an Environmental Performance Score (EPS) and issues interest rate discounts (Margin Ratchets) based on ESG materiality weightings adapted from the MSCI/Refinitiv framework.

The core logic operates as a pure, mathematically isolated function:

$$EPS=(S_\text{nat}\times0.30)+(E_\text{loc}\times0.70)$$

$$\text{Rate}_\text{final}=R_\text{base}-\left(\frac{\text{EPS}}{100}\times D_\text{max}\right)$$

## 🚀 Quick Start (Local Development)

This project includes a custom, DRY-compliant bash utility (`exec.sh`) that completely abstracts the complexity of Docker and `uv` environment management.

**1. Clone the repository and navigate to the root:**

```bash
git clone https://github.com/scAB1001/green-fintech-baas.git
cd green-fintech-baas

```

**2. Boot the infrastructure (PostgreSQL & Redis):**

```bash
# Spins up the required databases in isolated Docker containers
./exec.sh db-up

```

**3. Run Database Migrations & Seed Reference Data:**

```bash
# Automatically applies Alembic heads and seeds the mock JSON data
./exec.sh db-init

```

**4. Start the FastAPI Server:**

```bash
# Starts the Uvicorn server with hot-reloading enabled
./exec.sh api-up

```

The interactive API documentation is now live at: `http://localhost:8080/docs`

## 📡 API Endpoints

The API exposes 8 primary endpoints mapped to the `Company` domain. For full request/response payloads, please refer to the attached `API_Documentation.pdf`.

| Method   | Endpoint                                            | Description                               | Cache Behavior              |
| -------- | --------------------------------------------------- | ----------------------------------------- | --------------------------- |
| `POST`   | `/api/v1/companies/`                                | Ingests live data from OpenCorporates     | Triggers Cache Invalidation |
| `GET`    | `/api/v1/companies/`                                | Paginated list of all corporate entities  | Cached (List Pattern)       |
| `GET`    | `/api/v1/companies/{id}`                            | Fetch a specific company's details        | Cached (Entity Pattern)     |
| `PATCH`  | `/api/v1/companies/{id}`                            | Update specific corporate fields          | Triggers Cache Invalidation |
| `DELETE` | `/api/v1/companies/{id}`                            | Hard delete entity and cascade relations  | Triggers Cache Invalidation |
| `POST`   | `/api/v1/companies/{id}/simulate-loan`              | Executes ESG math engine for a loan quote | No Cache (State Mutation)   |
| `GET`    | `/api/v1/companies/export/csv`                      | Generates a bulk `text/csv` database dump | Cached (Text)               |
| `GET`    | `/api/v1/companies/{id}/simulate-loan/{sim_id}/pdf` | Renders an `application/pdf` formal quote | Cached (Base64 Binary)      |

## 🧪 Testing & Quality Assurance

The test suite mathematically proves the integrity of the database schema (unique constraints, cascading deletes), data boundaries (Pydantic validation), and business logic (cache hits/misses, external API fallbacks).

**Run the complete test suite with coverage reporting:**

```bash
./exec.sh cov

```

*Current Status: 48/48 Passing | 100% Coverage.*

**Run the automated cache diagnostics:**

```bash
# Proves performance gains via simulated load testing against Redis
./exec.sh rd-stat

```

## 📁 Project Structure

```text
.
├── src/app/
│   ├── api/v1/endpoints/  # FastAPI Routers (HTTP Layer)
│   ├── core/              # Global configs (Logger, Redis connection pools)
│   ├── models/            # SQLAlchemy 2.0 ORM definitions (Database Layer)
│   ├── schemas/           # Pydantic validation boundaries (Network Layer)
│   └── services/          # Pure Business Logic & External API orchestrators
├── tests/
│   ├── fixtures/          # JSON seed data for deterministic tests
│   ├── integration/       # Database & API Router tests
│   └── unit/              # Schema boundaries and pure math functions
├── .github/workflows/     # CI/CD Pipelines (Release & Testing)
├── Dockerfile             # Multi-stage container definition
├── compose.yaml           # Local hybrid infrastructure
├── pyproject.toml         # UV dependency tree
└── exec.sh                # Interactive developer utility script

```

## 📄 License & Academic Honesty

Developed by @scAB1001. Submitted as coursework for the 2026 academic year.
Academic project - University of Leeds COMP3011 - Licensed under GPL-3.0
