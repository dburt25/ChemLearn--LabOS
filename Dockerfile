FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

ARG LABOS_HOME=/labos
WORKDIR ${LABOS_HOME}

RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
 && rm -rf /var/lib/apt/lists/*

# Create a non-root user for dev containers and runtime shells
RUN useradd --create-home --shell /bin/bash labos \
 && chown -R labos:labos ${LABOS_HOME}

# Copy resolver files separately to maximize Docker layer caching
COPY requirements.txt pyproject.toml README.md ./

RUN pip install --upgrade pip \
 && pip install --no-cache-dir -r requirements.txt

# Copy the full workspace and install LabOS in editable mode for CLI/UI use
COPY . ${LABOS_HOME}
RUN pip install --no-cache-dir -e . \
 && chown -R labos:labos ${LABOS_HOME}

USER labos
ENV PATH="/home/labos/.local/bin:${PATH}"

EXPOSE 8501

# Default to an interactive shell; run `streamlit run app.py` for the UI
CMD ["/bin/bash"]