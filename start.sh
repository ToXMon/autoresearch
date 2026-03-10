#!/usr/bin/env bash
# start.sh — container entrypoint for the AutoResearch Safe Starter
#
# This script is run by tini when the container starts. It prepares the
# working directories and then launches the autoresearch agent loop.
#
# IMPORTANT: Never put API keys or secrets in this file.
#            Pass secrets at runtime via environment variables, e.g.:
#              docker run -e ANTHROPIC_API_KEY=sk-... <image>
#            See README.md for full instructions.

set -euo pipefail

# ── Sanity-check required environment variables ──────────────────────────────
# These are set to defaults in the Dockerfile but can be overridden at runtime.
: "${APP_HOME:=/app}"
: "${DATA_DIR:=/data}"
: "${LOG_DIR:=/data/logs}"
: "${OUTPUT_DIR:=/data/output}"
: "${REPO_DIR:=/app/autoresearch}"

echo "==> AutoResearch Safe Starter"
echo "    APP_HOME   : $APP_HOME"
echo "    DATA_DIR   : $DATA_DIR"
echo "    LOG_DIR    : $LOG_DIR"
echo "    OUTPUT_DIR : $OUTPUT_DIR"
echo "    REPO_DIR   : $REPO_DIR"

# ── Ensure persistent directories exist ──────────────────────────────────────
# /data is expected to be a mounted volume on Akash so results survive restarts.
mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

# ── Move into the autoresearch repo ──────────────────────────────────────────
cd "$REPO_DIR"

# ── Install Python dependencies (uses uv, fast and reproducible) ─────────────
echo "==> Installing Python dependencies with uv..."
uv sync

# ── One-time data preparation ─────────────────────────────────────────────────
# prepare.py downloads training data and trains a BPE tokenizer.
# It is safe to re-run; it skips work that is already done.
echo "==> Running prepare.py (downloads data and trains tokenizer)..."
uv run prepare.py

# ── Launch the training experiment ───────────────────────────────────────────
# train.py runs a single 5-minute training experiment.
# The agent loop (if enabled) calls this repeatedly and tracks results.
echo "==> Starting training experiment..."
# Note: we intentionally do NOT use `exec` here because we pipe output through
# tee for logging. Using exec with a pipeline would replace the shell with tee
# (not the training process), which breaks tini's signal forwarding. The shell
# process stays alive to manage the pipeline, and tini can signal it cleanly.
uv run train.py 2>&1 | tee "$LOG_DIR/train_$(date +%Y%m%dT%H%M%S).log"
