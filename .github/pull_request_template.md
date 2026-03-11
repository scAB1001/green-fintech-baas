## 📝 Description

**Why is this change needed?**
* [Add your explanation here...]

* **What does this PR do? (List of changes)**
* _Added redis cache offsets and pagination_
* _Removed poetry from workflow *.yaml_
* [Add your changes here...]

## 🔗 Related Issue(s)

Closes #

## 🏷️ Type of Change

- [ ] 🐛 Bug fix (`fix:`)
- [ ] 🚀 New feature (`feat:`)
- [ ] 💥 Breaking change (Requires a major version bump)
- [ ] 🧹 Chore/Refactor (`chore:` or `refactor:`)
- [ ] 📝 Documentation update (`docs:`)
- [ ] 🧪 Test addition/update (`test:`)

## ✅ Quality Assurance & Security Checklist

**Code Standards & Security:**
- [ ] **Conventional Commits:** PR title strictly follows the `<type>: <description>` format.
- [ ] **Feature Branching:** PR branch strictly follows the `<type>/<issue-number>/<short-description>` format.
- [ ] **Pre-commit:** I have run `uv run pre-commit run --all-files` (Ruff/Black passed).
- [ ] **Security:** My code passed the local GitGuardian (`ggshield`) secret scan.
- [ ] **No Warnings:** My code produces no new compiler/linter warnings.

**Testing & Database:**
- [ ] **Unit/Integration Tests:** I have added/updated Pytest tests for these changes.
- [ ] **Cache Verification:** Router tests explicitly verify Redis cache hits/deletions.
- [ ] **Migrations:** If database schemas changed, I generated and tested an Alembic migration.

**Documentation:**
- [ ] **API Specs:** Pydantic schemas and FastAPI route docstrings are updated.
- [ ] **Wiki:** I have updated the GitHub Wiki if architectural changes were made.

---

## 📸 Proof of Work (Screenshots & Artifacts)

<details>
<summary><b>🐘 PostgreSQL State</b> (Click to expand)</summary>

</details>

<details>
<summary><b>🔄 Alembic Migrations</b> (Click to expand)</summary>

</details>

<details>
<summary><b>⚡ Redis Cache</b> (Click to expand)</summary>

</details>

<details>
<summary><b>🌐 FastAPI Swagger UI</b> (Click to expand)</summary>

</details>

<details>
<summary><b>🧪 Pytest Coverage & Results</b> (Click to expand)</summary>

</details>

## 📦 CI/CD Artifacts

* [ ] `scAB1001~green-fintech-baas~KNNWOM.dockerbuild`: [Verify]
* [ ] `ci-result-tests.zip`: [Insert Link Here]
* [ ] `ci-result-build.zip`: [Insert Link Here]
* [ ] `all-ci-results.zip`: [Insert Link Here]

## 💬 Additional Notes for Reviewer
