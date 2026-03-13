# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — AutoResearch Autonomous Agent for Akash
#
# This image runs karpathy/autoresearch with an autonomous AI research agent
# on a single NVIDIA GPU inside an Akash deployment.
#
# IMPORTANT: Never bake API keys or other secrets into this image.
#            Pass them at runtime via environment variables. See README.md.
# ─────────────────────────────────────────────────────────────────────────────

# ── Base image ───────────────────────────────────────────────────────────────
# NVIDIA CUDA runtime for PyTorch GPU support. cuda 12.4 pairs well with
# PyTorch ≥ 2.3 and covers H100 / A100 workloads.
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# ── Metadata ─────────────────────────────────────────────────────────────────
LABEL org.opencontainers.image.title="AutoResearch Autonomous Agent" \
      org.opencontainers.image.description="karpathy/autoresearch with autonomous AI research loop on Akash" \
      org.opencontainers.image.source="https://github.com/ToXMon/autoresearch"

# ── Environment defaults ──────────────────────────────────────────────────────
ENV APP_HOME=/app \
    DATA_DIR=/data \
    LOG_DIR=/data/logs \
    OUTPUT_DIR=/data/output \
    REPO_DIR=/app/autoresearch \
    PYTHONUNBUFFERED=1 \
    UV_CACHE_DIR=/root/.cache/uv \
    PIP_NO_INPUT=1 \
    DEBIAN_FRONTEND=noninteractive

# ── System packages ───────────────────────────────────────────────────────────
RUN apt-get update && apt-get install -y --no-install-recommends \
        python3 \
        python3-pip \
        git \
        curl \
        ca-certificates \
        tini \
        bash \
    && rm -rf /var/lib/apt/lists/*

# ── Install uv ────────────────────────────────────────────────────────────────
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

# ── Clone karpathy/autoresearch ───────────────────────────────────────────────
RUN mkdir -p "$APP_HOME" \
    && git clone --depth 1 https://github.com/karpathy/autoresearch "$REPO_DIR"

# ── Copy autonomous agent files ───────────────────────────────────────────────
# Copy the agent loop, monitor server, and start script into the repo
COPY agent_loop.py "$REPO_DIR/agent_loop.py"
COPY monitor_server.py "$REPO_DIR/monitor_server.py"
COPY start.sh /start.sh
RUN chmod +x /start.sh

# ── Create persistent data directories ───────────────────────────────────────
RUN mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR $APP_HOME

# ── Entrypoint ────────────────────────────────────────────────────────────────
ENTRYPOINT ["/usr/bin/tini", "--", "/start.sh"]
