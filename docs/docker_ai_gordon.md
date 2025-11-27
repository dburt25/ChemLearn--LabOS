# Docker AI ("Gordon") and Docker Scout Playbook

This guide distills the Gordon chat transcript into concrete steps you can follow to analyze the LabOS container images, improve the Dockerfile, and continuously monitor security posture.

## 1. Inspect and optimize running containers
Use Docker AI's natural-language interface to review live containers. Replace the ID with the one from `docker ps`.

```bash
docker ai "Analyze my running container with ID <container-id>"
```

Gordon reports CPU, memory, networking, and configuration insights along with suggested remediations (e.g., missing health checks or over-provisioned resources).

## 2. Rate and improve the Dockerfile
Feed the LabOS `Dockerfile` to Gordon for automated best-practice checks such as cache usage, layer ordering, and security hardening.

```bash
docker ai rate my Dockerfile
```

Review the scorecard and apply the recommendations (multi-stage builds, pinning digests, environment variable hygiene, etc.). Re-run the command until the score stabilizes.

## 3. Scan for vulnerabilities with Docker Scout
Run Docker Scout's CVE scanner against either a running container (`docker ps --quiet`) or a tagged image.

```bash
docker scout cves <image-or-id>
```

Add `--only-severity critical,high --exit-code` inside CI to enforce gating on serious vulnerabilities.

## 4. Optimize multi-service stacks
When working with `docker-compose.yml`, ask Gordon to audit the stack holistically.

```bash
docker ai "Optimize my docker-compose.yml for best practices"
```

Typical suggestions include introducing health checks, constraining resource limits, moving secrets into `.env`, and splitting build contexts.

## 5. Troubleshoot container issues
Delegate debugging questions to Gordon when containers misbehave.

```bash
docker ai "Troubleshoot my container with ID <container-id>"
```

Describe observed symptoms (crashes, missing env vars, failing probes) for targeted guidance.

## 6. Migrate toward Hardened Images (DHI)
Gordon can draft a hardened variant of the Dockerfile that swaps the base image for Docker Hardened Images (DHI) and tightens permissions.

```bash
docker ai "Migrate my Dockerfile to DHI"
```

Follow up by pinning the resulting digest and validating functionality before promoting the change.

## 7. Continuous monitoring via Docker Desktop
Enable Docker Desktop's **Ask Gordon** tab (✨ icon next to a container) to receive real-time advice, anomaly detection, and update reminders without leaving the UI.

## 8. Stay updated
Prompt Gordon to check for tooling and image updates when planning maintenance windows.

```bash
docker ai "Check for updates to Docker Desktop and my images"
```

## 9. Running the Docker Scout CLI container locally
This repository now includes a `docker-scout` helper service to satisfy the "install this container" request.

```bash
docker compose run --rm docker-scout --help
```

The service pulls [`docker/scout-cli`](https://github.com/docker/scout-cli) and mounts the Docker socket so you can execute commands such as:

```bash
docker compose run --rm docker-scout cves labos-dev:latest --only-severity critical,high
```

> **Note:** On Windows with Docker Desktop, the socket mount in `docker-compose.yml` still resolves to `/var/run/docker.sock`; Docker Desktop automatically maps it to the Hyper-V/WSL VM.

Authenticate the helper by exporting secrets before running Compose (or by copying `.env.example` to `.env` in the repo root):

```env
DOCKER_HUB_USER=<your-docker-id>
DOCKER_HUB_PAT=<personal-access-token>
```

Those values are passed into the container as `DOCKER_SCOUT_HUB_USER` / `DOCKER_SCOUT_HUB_PASSWORD`, avoiding reliance on host credential stores that `docker-scout` cannot access inside the container.

Environment overrides:

- `DOCKER_SCOUT_CACHE_DIR` – reuse SBOM caches between runs (default: `/tmp/scout-cache`).
- `DOCKER_SCOUT_NO_CACHE=true` – disable caching entirely.
- `DOCKER_SCOUT_REGISTRY_USER` / `DOCKER_SCOUT_REGISTRY_PASSWORD` – provide registry credentials for private bases.

## 10. Recommended CI wiring
Pair the CLI with CI platforms (GitHub Actions, GitLab, Jenkins, etc.) to stop builds that introduce new CVEs. The official repo documents ready-made workflow snippets if you need deeper integration.

By following the flow above, you can loop between Gordon's qualitative advice and Docker Scout's quantitative findings to keep LabOS images lean, secure, and compliant.
