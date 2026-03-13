# AutoResearch-Akash Verification Checklist

## Pre-Deployment Checklist

### ✅ Required Secrets (set at deploy time)
- [ ] **LLM_API_KEY** - Your LLM provider API key (Anthropic or OpenAI)
- [ ] **GitHub Personal Access Token** (optional) - For pushing results to a fork

### ✅ Required Environment Variables
| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_API_KEY` | ✅ Yes | - | API key for LLM provider |
| `LLM_PROVIDER` | ✅ Yes | `anthropic` | Provider: `anthropic` or `openai` |
| `MODEL_NAME` | ✅ Yes | `claude-3-7-sonnet-20250219` | Model identifier |
| `LLM_API_BASE` | No | `` | Custom API endpoint (leave empty for default) |
| `MAX_ITERS` | No | `25` | Number of experiment iterations |
| `EXPERIMENT_TIMEOUT_SECONDS` | No | `900` | Timeout per training run (15 min) |
| `RUN_MODE` | No | `agent` | `agent` or `prepare-only` |

### ✅ Docker Image Requirements
- [ ] Image built from project Dockerfile
- [ ] Image pushed to accessible registry (ghcr.io, Docker Hub, etc.)
- [ ] Image tag updated in `deploy.yaml`

### ✅ Akash SDL Verification
- [ ] `deploy.yaml` version is `2.0`
- [ ] GPU units set to `1` with `vendor: nvidia`
- [ ] Persistent storage `100Gi` mounted at `/data`
- [ ] Memory `16Gi` minimum
- [ ] CPU `4` units minimum
- [ ] Signed by auditors enabled for provider trust

---

## Deployment Steps (Akash Console)

### Step 1: Build and Push Docker Image

```bash
# Build the image
docker build -t your-registry/autoresearch:latest .

# Push to registry
docker push your-registry/autoresearch:latest
```

### Step 2: Update deploy.yaml

Replace the image placeholder:
```yaml
image: your-registry/autoresearch:latest
```

### Step 3: Deploy via Akash Console

1. Go to [console.akash.network](https://console.akash.network)
2. Connect your wallet (Keplr or Leap)
3. Click "Create Deployment"
4. Paste the contents of `deploy.yaml`
5. Set your `LLM_API_KEY` in the environment section
6. Choose a provider with GPU availability
7. Click "Deploy"

### Step 4: Monitor Deployment

1. Watch the logs in Akash Console
2. Look for:
   - `==> Installing Python dependencies with uv...`
   - `==> Running prepare.py...`
   - `==> Starting autonomous research agent...`

---

## How to Verify It's Working

### Container Startup Indicators

Look for these log messages in order:

```
==> AutoResearch Autonomous Agent
    APP_HOME   : /app
    DATA_DIR   : /data
    REPO_DIR   : /app/autoresearch
    ...
==> Installing Python dependencies with uv...
==> Installing litellm for LLM API calls...
==> Running prepare.py (downloads data and trains tokenizer)...
==> Initializing results.tsv
==> Starting autonomous research agent...
```

### Training Loop Indicators

Each iteration shows:

```
============================================================
ITERATION 1/25
============================================================
[INFO] Calling LLM to generate experiment...
[INFO] Experiment: <description of proposed change>
[INFO] Running training (timeout: 900s)...
[SUCCESS] Training completed in 320.5s
[SUCCESS] Logged result: keep - val_bpb=2.345678
```

### Status Types

| Status | Meaning | Action Taken |
|--------|---------|--------------|
| `keep` | val_bpb improved | Changes kept, new baseline |
| `discard` | No improvement | Reverted to previous commit |
| `crash` | Training failed | Reverted to previous commit |

---

## How to Check Results

### Method 1: Akash Console Logs

View live logs in Akash Console deployment page.

### Method 2: Persistent Storage (results.tsv)

The results file is stored at `/data/output/results.tsv`:

```tsv
commitval_bpbmemory_gbstatusdescription
abc12342.34567812.5keepAdded layer normalization
def56782.45678911.2discardIncreased learning rate
```

### Method 3: Download Logs via kubectl (if available)

```bash
kubectl exec -it <pod-name> -- cat /data/output/results.tsv
```

### Method 4: Visualize Results

Run the visualization script:

```bash
python visualize_results.py /data/output/results.tsv
```

---

## Troubleshooting

### Issue: Container exits immediately

**Cause**: Missing required environment variable

**Solution**: Ensure `LLM_API_KEY`, `LLM_PROVIDER`, and `MODEL_NAME` are set

### Issue: Training crashes with CUDA OOM

**Cause**: GPU memory exceeded

**Solution**: 
- The agent will auto-revert crashed experiments
- If persistent, reduce model size in train.py baseline

### Issue: prepare.py hangs

**Cause**: Download timeout or network issue

**Solution**: 
- Check provider network connectivity
- Data shards are ~500MB total

### Issue: LLM API calls fail

**Cause**: Invalid API key or rate limit

**Solution**: 
- Verify `LLM_API_KEY` is correct
- Check API rate limits
- Agent will retry on failures

### Issue: No improvement after many iterations

**Cause**: Normal - optimization is hard!

**Solution**: 
- This is expected behavior
- Agent explores different approaches
- Best result is preserved in results.tsv

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Akash Deployment                         │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐     │
│  │   start.sh  │───>│ prepare.py  │───>│agent_loop.py│     │
│  │ (entrypoint)│    │ (data prep) │    │ (main loop) │     │
│  └─────────────┘    └─────────────┘    └──────┬──────┘     │
│                                               │             │
│                     ┌─────────────────────────┼─────┐      │
│                     │                         v     │      │
│                     │  ┌─────────┐    ┌───────────┐ │      │
│                     │  │train.py │<───│  LLM API  │ │      │
│                     │  │(modify) │    │(generate) │ │      │
│                     │  └────┬────┘    └───────────┘ │      │
│                     │       │                       │      │
│                     │       v                       │      │
│                     │  ┌─────────┐                  │      │
│                     │  │ results │<─────────────────┘      │
│                     │  │   .tsv  │                         │
│                     │  └─────────┘                         │
│                     │         │                           │
│                     └─────────┼───────────────────────────┘
│                               │                            │
│                     ┌─────────v─────────┐                 │
│                     │ Persistent Volume │                 │
│                     │     (/data)       │                 │
│                     │  - /data/logs     │                 │
│                     │  - /data/output   │                 │
│                     └───────────────────┘                 │
└─────────────────────────────────────────────────────────────┘
```

---

## File Locations in Container

| Path | Purpose | Persistent |
|------|---------|------------|
| `/app/autoresearch` | Cloned karpathy/autoresearch repo | No |
| `/app/autoresearch/train.py` | Training script (modified by agent) | No |
| `/app/autoresearch/agent_loop.py` | Autonomous agent loop | No |
| `/data` | Persistent storage mount | **Yes** |
| `/data/logs` | Training and agent logs | **Yes** |
| `/data/output/results.tsv` | Experiment results | **Yes** |
| `/root/.cache/autoresearch` | Downloaded training data | No |

---

## Production Recommendations

1. **Use dedicated Akash account** - Separate from main wallet
2. **Set spending limits** - Prevent unexpected costs
3. **Monitor first run** - Watch logs for the first few iterations
4. **Backup results** - Download results.tsv periodically
5. **Use trusted providers** - Keep signedBy in deploy.yaml

---

## Quick Reference Commands

```bash
# Build Docker image
docker build -t autoresearch:latest .

# Test locally (requires GPU)
docker run --gpus all -e LLM_API_KEY=your_key -e LLM_PROVIDER=anthropic -e MODEL_NAME=claude-3-7-sonnet-20250219 autoresearch:latest

# Validate SDL
akash sdl validate deploy.yaml

# Check file syntax
python3 -m py_compile agent_loop.py
bash -n start.sh
```

---

**Verified by**: DevOps Review  
**Date**: 2026-03-13  
**Status**: ✅ Ready for Production Deployment
