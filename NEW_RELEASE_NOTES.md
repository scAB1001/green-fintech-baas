## Release Notes

---
Released on 2026-03-24.

### 🚀 Features
- Production ready release (#10)

### 🐛 Bug Fixes
- Update ci.yaml to fail on error and use codecov token (#37)

### 🧹 Chores & Other Changes
- Add second code cov upload for analytics (#41)
- Update Documentation
- release v1.3.0 (#27)
- Update Documentation
- release v1.3.0 (#25)
- Add Dependabot configuration for updates

### 👥 Contributors
- @scAB1001

### 🐳 Deploy Green FinTech BaaS v1.3.0

---

#### Pull the prebuilt Docker Image
The immutable container for this release is hosted on the GCHR (GitHub Container Registry).
```bash
docker pull ghcr.io/scAB1001/green-fintech-baas:v1.3.0
```
#### Verifying GitHub Artifact Attestations
The Docker images in this release have provenance attestations generated with GitHub Actions. These can be verified by using the GitHub CLI:
```bash
gh attestation verify ghcr.io/scAB1001/green-fintech-baas:v1.3.0 --repo scAB1001/green-fintech-baas
```
