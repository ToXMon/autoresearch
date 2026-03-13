#!/usr/bin/env bash
# start.sh — AutoResearch Autonomous Agent for Akash
#
# This script is run by tini when the container starts. It validates the
# runtime configuration, prepares the repository, and runs the autonomous
# research agent loop.
#
# IMPORTANT: Never put API keys or secrets in this file.
#            Pass secrets at runtime via environment variables.

set -euo pipefail

# ── Runtime configuration ─────────────────────────────────────────────────────
: "${APP_HOME:=/app}"
: "${REPO_DIR:=/app/autoresearch}"
: "${DATA_DIR:=/data}"
: "${LOG_DIR:=/data/logs}"
: "${OUTPUT_DIR:=/data/output}"
: "${RUN_MODE:=agent}"
: "${MAX_ITERS:=25}"
: "${EXPERIMENT_TIMEOUT_SECONDS:=900}"

prepare_log_path="$LOG_DIR/prepare.log"
agent_log_path="$LOG_DIR/agent.log"

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
if [[ -z "${LLM_API_KEY:-}" ]]; then
    cat >&2 <<'EOF'
ERROR: LLM_API_KEY is not set.
The autonomous agent needs an LLM API key to generate experiments.

Set LLM_API_KEY in your Docker environment or Akash SDL secret/env section.
EOF
    exit 1
fi

require_non_empty \
    "LLM_PROVIDER" \
    "Set LLM_PROVIDER to your API service name, for example: anthropic or openai."
require_non_empty \
    "MODEL_NAME" \
    "Set MODEL_NAME to the model the agent should call, for example: claude-3-7-sonnet-20250219."

# ── Ensure persistent directories exist ───────────────────────────────────────
mkdir -p "$DATA_DIR" "$LOG_DIR" "$OUTPUT_DIR"

if [[ ! -d "$REPO_DIR" ]]; then
    printf 'ERROR: REPO_DIR does not exist: %s\n' "$REPO_DIR" >&2
    exit 1
fi

echo "==> AutoResearch Autonomous Agent"
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

# ── Move into the autoresearch repo ──────────────────────────────────────────
cd "$REPO_DIR"

# ── Install Python dependencies ───────────────────────────────────────────────
echo "==> Installing Python dependencies with uv..."
uv sync

# ── Install litellm for multi-provider LLM support ─────────────────────────────
echo "==> Installing litellm for LLM API calls..."
uv pip install litellm --quiet || echo "litellm installation failed, will use direct API calls"

# ── One-time data preparation ─────────────────────────────────────────────────
echo "==> Running prepare.py (downloads data and trains tokenizer)..."
echo "    Logging prepare output to $prepare_log_path"
uv run prepare.py 2>&1 | tee "$prepare_log_path"

# ── Initialize results.tsv if needed ───────────────────────────────────────────
if [[ ! -f "$OUTPUT_DIR/results.tsv" ]]; then
    echo "==> Initializing results.tsv"
    echo -e "commit\tval_bpb\tmemory_gb\tstatus\tdescription" > "$OUTPUT_DIR/results.tsv"
fi

# ── Run the autonomous agent loop ─────────────────────────────────────────────
case "$RUN_MODE" in
    agent)
        cat <<EOF
==> Starting autonomous research agent...
    - LLM Provider: LLM_PROVIDER
    - Model: MODEL_NAME
    - Max iterations: MAX_ITERS
    - Experiment timeout: EXPERIMENT_TIMEOUT_SECONDS seconds
    - Logs: LOG_DIR
EOF
        echo "==> Running agent_loop.py..."
        exec uv run python agent_loop.py 2>&1 | tee "$agent_log_path"
        ;;
    prepare-only)
        echo "==> Prepare-only mode: data prepared, container staying alive."
        exec tail -f /dev/null
        ;;
    *)
        printf 'ERROR: Unsupported RUN_MODE: %s\nUse RUN_MODE=agent or RUN_MODE=prepare-only.\n' "$RUN_MODE" >&2
        exit 1
        ;;
esac
