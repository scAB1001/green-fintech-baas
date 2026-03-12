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

## 🗺️ System Architecture

```mermaid
graph TD
    Client([Client / Swagger UI]) -->|HTTP REST| API[FastAPI Server]

    subgraph Containerized Backend
        API -->|Async I/O| Cache[(Redis Cache)]
        API -->|SQLAlchemy 2.0| DB[(PostgreSQL 18)]

        subgraph Business Logic
            API -.-> MathEngine[ESG Simulation Engine]
            API -.-> PDFService[ReportLab PDF Generator]
        end
    end

    API -->|Live Entity Verification| External[OpenCorporates API]
    MathEngine -.-> MacroData[UK Gov Emissions & Grid Data]

```

## ⚙️ Core Mathematical Engine

The API calculates an Environmental Performance Score (EPS) and issues interest rate discounts (Margin Ratchets) based on ESG materiality weightings adapted from the MSCI/Refinitiv framework.

The core logic operates as a pure, mathematically isolated function:

$$\text{EPS}=(S_\text{nat}\times0.30)+(E_\text{loc}\times0.70)$$

$$\text{Rate}_\text{final}=R_\text{base}-\left(\frac{\text{EPS}}{100}\times D_\text{max}\right)$$

## 💻 Prerequisites & Target Environment

This platform is engineered for modern, containerized workflows. To guarantee deterministic execution, ensure your local development environment meets the following requirements before cloning the repository:

**Required Software & Tooling:**

* **Python 3.12:** Installed and configured in your system PATH.
* **uv (Astral):** Our primary package manager. It replaces `pip` and `poetry`, reading the provided `uv.lock` file to install the exact dependency tree in milliseconds.
* **Docker & Docker Compose:** Essential for spinning up the isolated `green-fintech-db` (PostgreSQL) and `green-fintech-cache` (Redis) containers without polluting your host machine.
* **Git:** For version control and cloning the repository.
* **IDE:** Visual Studio Code (VS Code) or any equivalent modern IDE.
* **Local PostgreSQL Client (Optional):** While Docker runs the database engine, having local `psql` tools can be helpful for direct inspection.
* **GitGuardian (Optional):** Recommended for local secret scanning to prevent accidental token commits.

**Target Machine Specification (Certified Local Environment):**

The local orchestration scripts and hybrid container configurations were designed and verified against the following Linux development environment:

* **OS:** Linux Mint 22.3 (Ubuntu 24.04 base) | Kernel 6.17.0 x86_64
* **Compute:** AMD Ryzen 5 7520U (Quad Core, Boost 4.3GHz) | 32.0 GB Physical RAM
* **Compiler/Runtime:** GCC v13.3.0 | Python 3.12

---

## 🔑 External Dependencies: Data Sourcing

### OpenCorporates API

To actively ingest live corporate data, this project requires an OpenCorporates API Key.

As an academic project, you qualify for their **Public Benefit** tier. You must create an account and submit the [Public Benefit Projects Form](https://opencorporates.atlassian.net/servicedesk/customer/portal/4/group/16/create/36) using your university or organizational email address.

* **Rate Limits:** At the time of this documentation, the Public Benefit tier allows for up to 10,000 calls per day and 50,000 calls per month.
* **Licensing & Attribution:** OpenCorporates data is provided under strict open-data licenses. If you publish or publicly deploy this project, **explicit attribution to OpenCorporates is legally required**. Please review their [Self-Service API Terms of Service](https://opencorporates.com/legal-information/self-service-api-terms-of-service/) and [General Terms of Use](https://opencorporates.com/terms-of-use-2/).

### Gov UK Statistics

To pull the regional static emissions data metrics, navigate to the public, open-source [UK local authority and regional greenhouse gas emissions statistics, 2005 to 2023](https://www.gov.uk/government/statistics/uk-local-authority-and-regional-greenhouse-gas-emissions-statistics-2005-to-2023) or newer.

* **Download the MS Excel Spreadsheet:** Verify that sheet '1_1' adheres to and contains 'Table 1.1: Local authority territorial greenhouse gas emissions estimates 2005-2023 (kt CO2e) - Full dataset'
* **Modify `scripts/seed_db.py` if named otherwise:** Update the sheet name on line 109 to the correct name: `sheet_name="1_1"`.

---

## 🛠️ Project Decomposition (`scripts/`)

To adhere to the Single Responsibility Principle and avoid massive, unreadable bash files, the project's DevOps automation is heavily decomposed into the `scripts/` directory:

* `exec.sh`: The master interactive orchestrator menu. It manages global tasks like linting, workspace purging, and executing tests.
* `scripts/api-helper.sh`: Manages FastAPI container lifecycles, Uvicorn hot-reloading, and the interactive REST CRUD demonstration.
* `scripts/pg-helper.sh`: Handles Alembic state synchronization, database wiping, schema upgrades, and mock data seeding.
* `scripts/rd-helper.sh`: Manages Redis cache diagnostics and cache flushing.

---

## 🚀 Quick Start (Running the System)

The master `exec.sh` orchestrator completely abstracts the complexity of database migrations, network mapping, and package installation.

**1. Clone the repository and navigate to the root:**

```bash
git clone https://github.com/scAB1001/green-fintech-baas.git
cd green-fintech-baas

```

**2. Environment Configuration:**
The application requires specific environment variables to connect to the database, cache, and external APIs. Create a local `.env` file from the provided template:

```bash
cp .env.example .env

```

Ensure your `.env` contains at least the following baseline configurations (inserting your OpenCorporates key):

```ini
# .env
API_KEY=sk_test_greenfintech_123456
ENVIRONMENT=development  # or production
PROJECT_NAME="Green FinTech BaaS Simulator"
VERSION="1.3.0"

# Database Configuration (Matches compose.yaml)
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=green_fintech
POSTGRES_PORT=5432
POSTGRES_INITDB_ARGS=--auth=scram-sha-256
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/green_fintech

# Redis Configuration
REDIS_PASSWORD=dev_password
REDIS_URL=redis://:dev_password@localhost:6379

# External APIs
OPENCORPORATES_API_KEY=your_development_key_here

```

**3. Initialize the Python Workspace:**

It should look like this:
[![Watch the video](https://img.youtube.com/vi/Lk3Zn7-mzmw/maxresdefault.jpg)](https://youtu.be/Lk3Zn7-mzmw)

```bash
# Make the bash (*.sh) scripts executable
chmod +x ./exec.sh scripts/common.sh scripts/pg-helper.sh scripts/rd-helper.sh scripts/api-helper.sh

# Utilizes 'uv' to instantly read the lockfile, install all dependencies, and configure Git hooks
./exec.sh init

```

**4. Boot the Complete System Stack:**

```bash
# Builds the Docker network from scratch. It spins up the PostgreSQL database,
# the Redis cache, and the FastAPI service. It will interactively prompt you
# to run Alembic migrations and seed the database with mock entities.
./exec.sh stack

```

The system is now fully operational.

* **Interactive API Documentation:** `http://localhost:8080/docs`
* **Test the complete CRUD lifecycle:** Run `./exec.sh api-demo` in a new terminal to watch the system ingest companies, calculate SLL loans, render PDFs, and cascade deletions in real-time.

[![Watch the video](https://img.youtube.com/vi/0toaGT8ieck/maxresdefault.jpg)](https://youtu.be/0toaGT8ieck)

---

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

**Run the complete unit & integration test suite (Pytest):**

```bash
# Interactive to provide choices to test for coverage or to specify files/markers to test.
./exec.sh test

```

**Run the automated end-to-end architecture diagnostic:**

```bash
# Proves PostgreSQL, Redis, and FastAPI are communicating successfully
./exec.sh e2e

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
├── scripts/               # Decomposed DevOps and Orchestration helpers
├── tests/                 # Pytest suite (Unit & Integration)
├── .github/workflows/     # CI/CD Pipelines (Security, Release, Testing)
├── Dockerfile             # Multi-stage FastAPI container definition
├── compose.yaml           # Local hybrid infrastructure network
├── pyproject.toml         # UV dependency tree
└── exec.sh                # Master interactive developer utility script

```

## 🔮 Roadmap & Future Enhancements

While the current BaaS simulator is fully operational, a production-grade deployment would require the following evolutionary steps:

* **OAuth2 / OpenID Connect:** Implementing strict JWT-based authentication and Role-Based Access Control (RBAC) to differentiate between Bank Admins and Corporate Borrowers.
* **Advanced Rate Limiting:** Applying Redis-backed token bucket algorithms to protect the API from DDoS attacks and manage OpenCorporates API quota consumption.
* **Event-Driven Architecture:** Decoupling the PDF rendering engine into a background Celery or RabbitMQ worker queue to completely unblock the FastAPI event loop during high-load concurrency.
* **Remote Deployment:** Publishing the project to a service like Railway or MCP for public use and demonstration.

## 📄 License & Academic Honesty

Developed by @scAB1001, aided by AI models as per code: *GREEN* for AI usage.

Submitted as coursework for the 2026 academic year.

Academic project - University of Leeds COMP3011 - Licensed under GPL-3.0
