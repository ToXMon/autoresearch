#!/usr/bin/env bash
# start.sh — safe container entrypoint for the AutoResearch Safe Starter
#
# This script is run by tini when the container starts. It validates the
# runtime configuration, prepares the repository, and then keeps the container
# alive so an external orchestration layer or coding agent can attach later.
#
# IMPORTANT: Never put API keys or secrets in this file.
#            Pass secrets at runtime via environment variables.
#            See README.md for full instructions.

set -euo pipefail

# ── Runtime configuration ─────────────────────────────────────────────────────
# These defaults are safe for Akash deployments but can be overridden at
# runtime with environment variables.
: "${APP_HOME:=/app}"
: "${REPO_DIR:=/app/autoresearch}"
: "${DATA_DIR:=/data}"
: "${LOG_DIR:=/data/logs}"
: "${OUTPUT_DIR:=/data/output}"
: "${RUN_MODE:=agent}"
: "${MAX_ITERS:=25}"
: "${EXPERIMENT_TIMEOUT_SECONDS:=900}"

prepare_log_path="$LOG_DIR/prepare.log"

print_missing_var_error() {
    local variable_name="$1"
    local guidance="$2"
    printf 'ERROR: Missing required environment variable: %s\n%s\n' "$variable_name" "$guidance" >&2
}

require_non_empty() {
    local variable_name="$1"
    local guidance="$2"
    if [[ -z "${!variable_name:-}" ]]; then
        print_missing_var_error "$variable_name" "$guidance"
        exit 1
    fi
}

# ── Validate required LLM settings ────────────────────────────────────────────
# The starter does not print or store the API key. It only checks that the key
# exists so deployment mistakes are obvious before any orchestration begins.
if [[ -z "${LLM_API_KEY:-}" ]]; then
    cat >&2 <<'EOF'
ERROR: LLM_API_KEY is not set.
This starter needs an LLM API key so your coding agent or orchestration layer
can talk to the model provider later.

Set LLM_API_KEY in your Docker environment or Akash SDL secret/env section and
restart the container. The key is not stored in the image or printed in logs.
EOF
    exit 1
fi

require_non_empty \
    "LLM_PROVIDER" \
    "Set LLM_PROVIDER to your API service name, for example: anthropic or openai."
require_non_empty \
    "MODEL_NAME" \
    "Set MODEL_NAME to the model your orchestration layer should call, for example: claude-3-7-sonnet-20250219."

# ── Ensure persistent directories exist ───────────────────────────────────────
# /data is expected to be a mounted volume on Akash so logs and outputs survive
# restarts. Creating the directories here also keeps local Docker runs simple.
mkdir -p "$DATA_DIR" "$LOG_DIR" "$OUTPUT_DIR"

if [[ ! -d "$REPO_DIR" ]]; then
    printf 'ERROR: REPO_DIR does not exist: %s\n' "$REPO_DIR" >&2
    exit 1
fi

echo "==> AutoResearch Safe Starter"
echo "    APP_HOME   : $APP_HOME"
echo "    DATA_DIR   : $DATA_DIR"
echo "    LOG_DIR    : $LOG_DIR"
echo "    OUTPUT_DIR : $OUTPUT_DIR"
echo "    REPO_DIR   : $REPO_DIR"
echo "    RUN_MODE   : $RUN_MODE"
echo "    MAX_ITERS  : $MAX_ITERS"
echo "    EXPERIMENT_TIMEOUT_SECONDS : $EXPERIMENT_TIMEOUT_SECONDS"
echo "    LLM_PROVIDER : $LLM_PROVIDER"
echo "    MODEL_NAME   : $MODEL_NAME"
echo "    LLM_API_KEY  : [set]"
echo "    PREPARE_LOG  : $prepare_log_path"

# ── Move into the autoresearch repo ──────────────────────────────────────────
cd "$REPO_DIR"

# ── Install Python dependencies (uses uv, fast and reproducible) ─────────────
echo "==> Installing Python dependencies with uv..."
uv sync

# ── One-time data preparation ─────────────────────────────────────────────────
# prepare.py downloads training data and trains a BPE tokenizer.
# It is safe to re-run; it skips work that is already done.
echo "==> Running prepare.py (downloads data and trains tokenizer)..."
echo "    Logging prepare output to $prepare_log_path"
uv run prepare.py 2>&1 | tee "$prepare_log_path"

# ── Safe first-pass agent mode ────────────────────────────────────────────────
# In this initial starter version we do the safe setup work, print clear next
# steps, and keep the container alive for later orchestration.
case "$RUN_MODE" in
    agent)
        cat <<EOF
==> Agent mode is ready.
    - Repository preparation finished successfully.
    - No autonomous experiment loop has been started by start.sh yet.
    - Attach your orchestration layer or coding agent to this running container.
    - The agent should read LLM_PROVIDER and MODEL_NAME from the environment.
    - MAX_ITERS and EXPERIMENT_TIMEOUT_SECONDS are available for later use.
EOF
        echo "==> Keeping the container alive for later orchestration..."
        # exec replaces the shell with a simple long-running process so tini can
        # forward signals cleanly when the container is stopped.
        exec tail -f /dev/null
        ;;
    *)
        printf 'ERROR: Unsupported RUN_MODE: %s\nUse RUN_MODE=agent for this starter.\n' "$RUN_MODE" >&2
        exit 1
        ;;
esac
