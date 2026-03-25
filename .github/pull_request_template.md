## 📝 Description

**Why is this change needed?**
* [Add your explanation here...]

* **What does this PR do? (List of changes)**
* _[e.g., Added redis cache offsets and pagination]_
* _[e.g., Removed poetry from workflow *.yaml]_
* [Add your changes here...]

## 🔗 Related Issue(s)

Closes #

---

## 🏷️ Type of Change

- [ ] 🐛 **Bug fix** (`fix:`)
- [ ] 🚀 **New feature** (`feat:`)
- [ ] 💥 **Breaking change** (Requires a major version bump)
- [ ] 🧹 **Chore/Refactor** (`chore:` or `refactor:`)
- [ ] 🧪 **Test addition/update** (`test:`)

---

## ✅ Quality Assurance & Security Checklist

**Code Standards & Security:**
- [ ] **Conventional Commits:** PR title follows `<type>: <description>`.
- [ ] **Feature Branching:** PR branch follows `<type>/<issue-number>/<short-description>`.
- [ ] **Pre-commit:** I have run `uv run pre-commit run --all-files` (Ruff/Mypy/Black passed).
- [ ] **Security:** Code passed the local GitGuardian (`ggshield`) scan (No secrets leaked).
- [ ] **Auth:** New endpoints are secured with the `X-API-Key` dependency.
- [ ] **No Warnings:** My code produces no new compiler/linter warnings.

**Testing & Coverage:**
- [ ] **Tests:** I have added unit/integration tests for these changes.
- [ ] **Codecov:** I have checked the PR comment; coverage meets the **80% threshold**.
- [ ] **Test Analytics:** No new flaky tests or performance regressions in Codecov dashboard.
- [ ] **Database:** Migrations (Alembic) were generated and tested for schema changes.

**Documentation:**
- [ ] **API Specs:** ydantic schemas and FastAPI docstrings reflect these changes.
- [ ] **Wiki:** Relevant GitHub Wiki pages have been updated.

---

## 📊 Coverage & Analytics (Codecov)

| Metric              | Status                                                                         |
| :------------------ | :----------------------------------------------------------------------------- |
| **Total Coverage**  | % (Check PR Comment)                                                           |
| **Test Analytics**  | [View Failures/Flakes](https://app.codecov.io/gh/scAB1001/green-fintech-baas/) |
| **Build Artifacts** | Verified ✅                                                                     |

---

## 📸 Proof of Work (Screenshots & Artifacts)

<details>
<summary><b>🧪 Pytest Coverage & Results</b> (Click to expand)</summary>

```bash
# Paste summary from pytest-output.txt or coverage report here

```
</details>

<details>
<summary><b>🐘 PostgreSQL and ⚡ Redis State</b> (Click to expand)</summary>

</details>

<details>
<summary><b>🔄 Alembic Migrations</b> (Click to expand)</summary>

</details>

<details>
<summary><b>🌐 FastAPI Swagger UI</b> (Click to expand)</summary>

</details>

-----

## 📦 CI/CD Artifacts

  * [ ] **Consolidated Results:** `all-ci-results.zip` (Check "Actions" tab)
  * [ ] **Docker Image:** `ghcr.io/scab1001/green-fintech-baas:latest`

## 💬 Additional Notes for Reviewer
