#!/usr/bin/env bash
set -euo pipefail

IMAGE_NAME=${LABOS_IMAGE:-labos-dev}
APP_PORT=${LABOS_PORT:-8501}
WORKDIR=${LABOS_WORKDIR:-/labos}

if [[ $(basename "$(pwd)") != "1. LabOS" ]]; then
  echo "[docker-run] Run this script from the repository root (found $(pwd))." >&2
  exit 1
fi

CMD_TO_RUN=${*:-/bin/bash}

echo "[docker-run] Building image ${IMAGE_NAME} ..."
docker build -t "${IMAGE_NAME}" .

echo "[docker-run] Starting container on port ${APP_PORT} ..."
docker run \
  --rm \
  -it \
  -p "${APP_PORT}:8501" \
  -v "$(pwd):${WORKDIR}" \
  "${IMAGE_NAME}" \
  /bin/bash -lc "${CMD_TO_RUN}"
