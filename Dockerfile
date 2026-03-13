# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — AutoResearch Autonomous Agent for Akash
# ─────────────────────────────────────────────────────────────────────────────

FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

LABEL org.opencontainers.image.title="AutoResearch Autonomous Agent" \
      org.opencontainers.image.description="karpathy/autoresearch with autonomous AI research loop on Akash" \
      org.opencontainers.image.source="https://github.com/ToXMon/autoresearch"

ENV APP_HOME=/app \
    DATA_DIR=/data \
    LOG_DIR=/data/logs \
    OUTPUT_DIR=/data/output \
    REPO_DIR=/app/autoresearch \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/root/.cache/uv \
    PIP_NO_INPUT=1 \
    DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        git \
        curl \
        ca-certificates \
        tini \
        bash \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

RUN mkdir -p "$APP_HOME" \
    && git clone --depth 1 https://github.com/karpathy/autoresearch "$REPO_DIR"

# Cache bust - must be before COPY commands to invalidate cache
ARG CACHE_BUST=1

# Copy autonomous agent files - cache will be busted by CACHE_BUST arg
COPY agent_loop.py "$REPO_DIR/agent_loop.py"
COPY monitor_server.py "$REPO_DIR/monitor_server.py"
COPY start.sh /start.sh
RUN chmod +x /start.sh

RUN mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

WORKDIR $APP_HOME

ENTRYPOINT ["/usr/bin/tini", "--", "/start.sh"]
