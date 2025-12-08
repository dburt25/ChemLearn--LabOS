FROM python:3.11.6-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ARG LABOS_HOME=/labos
WORKDIR ${LABOS_HOME}

ARG DEBIAN_FRONTEND=noninteractive
RUN ap update \
 && apt-get install -y --no-install-recommends \
     build-essential=12.9 \
     git=1:2.39.5-0+deb12u2 \
 && rm -rf /var/lib/apt/lists/*

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:${PATH}"

# Copy resolver files separately to maximize Docker layer caching
COPY requirements.base.txt requirements.txt pyproject.toml README.md ./

RUN pip install --upgrade pip \
 && pip install --no-cache-dir --upgrade setuptools==78.1.1 \
 && pip install --no-cache-dir -r requirements.base.txt

# Copy the full workspace and install LabOS in editable mode for CLI/UI use
COPY . ${LABOS_HOME}
RUN pip install --no-cache-dir -e .


FROM python:3.11.6-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ARG LABOS_HOME=/labos
WORKDIR ${LABOS_HOME}

ARG DEBIAN_FRONTEND=noninteractive

# Create a non-root user for dev containers and runtime shells
RUN useradd --create-home --shell /bin/bash labos

RUN apt-get update \
 && apt-get install -y --no-install-recommends --only-upgrade \
     libc6 \
     libexpat1 \
     libssl3 \
     openssl \
     libkrb5-3 \
     libk5crypto3 \
     libgssapi-krb5-2 \
     libgnutls30 \
    libsystemd0 \
     sqlite3 \
     libsqlite3-0 \
     perl-base \
 && rm -rf /var/lib/apt/lists/*

RUN python -m pip install --no-cache-dir --upgrade pip setuptools==78.1.1

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder ${LABOS_HOME} ${LABOS_HOME}
RUN chown -R labos:labos ${LABOS_HOME}

USER labos
ENV PATH="/opt/venv/bin:/home/labos/.local/bin:${PATH}" \
    VIRTUAL_ENV="/opt/venv"

EXPOSE 8501

# Default to launching the Streamlit control panel; override CMD for ad-hoc shells
CMD ["streamlit", "run", "app.py", "--server.address", "0.0.0.0", "--server.port", "8501"]