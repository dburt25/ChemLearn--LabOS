# Archived Docker Setup

This directory contains Docker configurations from Phase 2.5.3 verification workflow.

## Contents
- `Dockerfile` - Multi-stage container build with hardened runtime
- `docker-compose.yml` - Compose setup with Streamlit + Docker Scout helper
- `.dockerignore` - Build context exclusions
- `scripts/docker-run.ps1` - Windows helper for ad-hoc container commands
- `scripts/docker-run.sh` - macOS/Linux helper for ad-hoc container commands
- `scripts/verify.ps1` - Full verification with Docker build, Gordon AI, Scout scan

## Why Archived?
Active development uses local `.venv` for maximum velocity:
- Tests run in **3-5 seconds** vs ~45s with Docker rebuild
- Code changes are **instant** (no rebuild cycle)
- Streamlit hot-reload works seamlessly
- No Docker Desktop overhead

## When to Resurrect
- CI/CD pipeline needs reproducible container builds
- Deployment to containerized environments
- Security scanning workflows (Docker Scout, Gordon AI)
- Multi-platform compatibility testing

## Migration Path
To restore Docker workflow:
1. Move files back to repo root
2. Update `.gitignore` to remove `.archive/` exclusion
3. Restore Docker sections in `README.md` and `DEVELOPMENT_GUIDE.md`
4. Run `docker build -t labos-dev .` to verify

## Preservation Date
December 7, 2025 - Archived during local dev optimization sprint.
