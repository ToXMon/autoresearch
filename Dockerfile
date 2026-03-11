# ─────────────────────────────────────────────────────────────────────────────
# Dockerfile — AutoResearch Safe Starter for Akash
#
# This image is designed to run karpathy/autoresearch on a single NVIDIA GPU
# inside an Akash deployment. It is intentionally kept simple and beginner-
# friendly. If you are new to Docker, read the "Docker design" section of
# README.md before making changes here.
#
# IMPORTANT: Never bake API keys or other secrets into this image.
#            Pass them at runtime via environment variables. See README.md.
# ─────────────────────────────────────────────────────────────────────────────

# ── Base image ───────────────────────────────────────────────────────────────
# We start from NVIDIA's official CUDA runtime image so that PyTorch can use
# the GPU. "devel" is not needed at runtime — "runtime" keeps the image lean.
# cuda 12.4 pairs well with PyTorch ≥ 2.3 and covers H100 / A100 workloads.
FROM nvidia/cuda:12.4.1-runtime-ubuntu22.04

# ── Metadata ─────────────────────────────────────────────────────────────────
LABEL org.opencontainers.image.title="AutoResearch Safe Starter" \
      org.opencontainers.image.description="karpathy/autoresearch on Akash, single-GPU" \
      org.opencontainers.image.source="https://github.com/ToXMon/autoresearch"

# ── Environment defaults ──────────────────────────────────────────────────────
# These can all be overridden at runtime with -e or in your Akash SDL.
# They are set here so every layer that follows can reference them consistently.
ENV APP_HOME=/app \
    DATA_DIR=/data \
    LOG_DIR=/data/logs \
    OUTPUT_DIR=/data/output \
    REPO_DIR=/app/autoresearch \
    # Keep Python output unbuffered so logs appear in real time.
    PYTHONUNBUFFERED=1 \
    # Tell uv where to find its cache (inside the container, not the host home).
    UV_CACHE_DIR=/root/.cache/uv \
    # Prevent pip from asking interactive questions.
    PIP_NO_INPUT=1 \
    DEBIAN_FRONTEND=noninteractive

# ── System packages ───────────────────────────────────────────────────────────
# We install the minimum set of tools needed to bootstrap the project:
#   • python3 / python3-pip — required by uv and the project itself
#   • git                   — to clone karpathy/autoresearch
#   • curl                  — to download the uv installer
#   • ca-certificates       — so https connections work correctly
#   • tini                  — lightweight init process (handles signals properly)
#   • bash                  — explicit dependency for start.sh
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
# uv is the fast Python package manager used by karpathy/autoresearch.
# We use the official installer script which pins a specific release.
# See https://docs.astral.sh/uv/getting-started/installation/
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
# The installer puts the binary in ~/.cargo/bin (or ~/.local/bin). Add both
# to PATH so that subsequent RUN commands and the entrypoint can find it.
ENV PATH="/root/.local/bin:/root/.cargo/bin:${PATH}"

# ── Clone karpathy/autoresearch ───────────────────────────────────────────────
# We clone the upstream repo at image build time so the image is self-contained.
# The agent will edit files inside this directory at runtime.
RUN mkdir -p "$APP_HOME" \
    && git clone --depth 1 https://github.com/karpathy/autoresearch "$REPO_DIR"

# ── Create persistent data directories ───────────────────────────────────────
# /data is expected to be a mounted volume on Akash so that logs and training
# outputs survive container restarts. We create the directories here so the
# image works even without a volume mount (e.g., during local testing).
RUN mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

# ── Copy the entrypoint script ────────────────────────────────────────────────
# start.sh validates runtime config, installs dependencies, and prepares the
# repository for later orchestration.
COPY start.sh /start.sh
RUN chmod +x /start.sh

# ── Working directory ─────────────────────────────────────────────────────────
WORKDIR $APP_HOME

# ── Entrypoint ────────────────────────────────────────────────────────────────
# tini is a tiny init process that correctly handles Unix signals (e.g., Ctrl-C)
# and reaps zombie processes. It wraps start.sh so the container shuts down
# cleanly when Akash stops the deployment, even when the starter is idling in
# its safe first-pass agent mode.
ENTRYPOINT ["/usr/bin/tini", "--", "/start.sh"]
