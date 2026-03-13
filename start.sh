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
: "${MONITOR_PORT:=8080}"

prepare_log_path="$LOG_DIR/prepare.log"
agent_log_path="$LOG_DIR/agent.log"
monitor_log_path="$LOG_DIR/monitor.log"

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

Set LLM_API_KEY in your Docker environment or Akash SDL env section.
For Anthropic: LLM_API_KEY=sk-ant-...
For OpenAI: LLM_API_KEY=sk-...
EOF
    exit 1
fi

# ── Create directories ────────────────────────────────────────────────────────
mkdir -p "$LOG_DIR" "$OUTPUT_DIR"

# ── Start monitor server in background ────────────────────────────────────────
echo "[$(date -Iseconds)] Starting monitor server on port $MONITOR_PORT..."
cd "$REPO_DIR"
python3 monitor_server.py "$MONITOR_PORT" > "$monitor_log_path" 2>&1 &
monitor_pid=$!
sleep 2
if kill -0 "$monitor_pid" 2>/dev/null; then
    echo "[$(date -Iseconds)] Monitor server started (PID: $monitor_pid)"
else
    echo "[$(date -Iseconds)] WARNING: Monitor server failed to start"
fi

# ── Run based on mode ─────────────────────────────────────────────────────────
cd "$REPO_DIR"

case "$RUN_MODE" in
    agent)
        echo "[$(date -Iseconds)] Starting autonomous research agent..."
        echo "[$(date -Iseconds)] Max iterations: $MAX_ITERS"
        echo "[$(date -Iseconds)] Experiment timeout: ${EXPERIMENT_TIMEOUT_SECONDS}s"
        exec python3 agent_loop.py
        ;;
    prepare-only)
        echo "[$(date -Iseconds)] Prepare-only mode, exiting."
        exit 0
        ;;
    monitor-only)
        echo "[$(date -Iseconds)] Monitor-only mode, keeping server running..."
        wait "$monitor_pid"
        ;;
    *)
        echo "ERROR: Unknown RUN_MODE: $RUN_MODE" >&2
        exit 1
        ;;
esac
