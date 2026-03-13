# 🚀 Quick Start: AutoResearch on Akash

Get an AI agent autonomously improving neural networks in 5 minutes!

## ⚡ Instant Demo (No Setup Required)

```bash
# See the demo immediately
./demo_quick.sh

# Or visualize results
python visualize_results.py
```

**What you'll see:**
- AI proposing experiments to improve neural network training
- Running 5-minute training on H100/A100 GPUs
- Tracking success/failure and keeping improvements
- 12% performance boost achieved autonomously!

---

## 🎯 Three Ways to Run

### 1. Local Docker (Testing)

```bash
# Build the image
docker build -t autoresearch-agent .

# Run with your API key
docker run --gpus all \
  -e LLM_PROVIDER=anthropic \
  -e MODEL_NAME=claude-3-7-sonnet-20250219 \
  -e LLM_API_KEY=sk-ant-your-key \
  -e MAX_ITERS=5 \
  autoresearch-agent
```

### 2. Akash Network (Production) 🌟

```bash
# 1. Build & push your image
./build.sh

# 2. Deploy via console.akash.network
# - Paste deploy.yaml
# - Set LLM_API_KEY
# - Select GPU provider
# - Deploy!
```

### 3. One-Command Akash

```bash
# Using Akash CLI
provider-services tx deployment create deploy.yaml \
  --from my-key \
  --chain-id akashnet-2
```

---

## 📊 What Happens During Deployment

```
┌─────────────────────────────────────────────────────────────┐
│ 1️⃣  Container starts on Akash GPU provider                  │
│     • Downloads training data (FineWeb-Edu 10B tokens)      │
│     • Trains BPE tokenizer                                  │
│     • Prepares CUDA environment                             │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 2️⃣  AI agent reads train.py                                 │
│     • Analyzes GPT architecture (Flash Attention 3)        │
│     • Understands current hyperparameters                   │
│     • Reviews past experiment results                       │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 3️⃣  Generate hypothesis                                     │
│     • "Add gradient clipping to stabilize training"        │
│     • "Try cosine learning rate schedule"                   │
│     • "Increase attention heads from 6 to 8"               │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 4️⃣  Run experiment (5 minutes)                              │
│     • Modifies train.py with hypothesis                     │
│     • Commits to git for version control                    │
│     • Runs training with 900s timeout                       │
│     • Measures val_bpb metric                               │
└─────────────────────────────────────────────────────────────┘
                            ▼
┌─────────────────────────────────────────────────────────────┐
│ 5️⃣  Evaluate & Iterate                                      │
│     ✅ Improved? → Keep changes, next experiment            │
│     ❌ Worse? → Git revert, try different hypothesis        │
│     💥 Crashed? → Log error, try safer approach             │
└─────────────────────────────────────────────────────────────┘
                            ▼
                      Repeat MAX_ITERS times
```

---

## 💰 Cost Breakdown

| Resource | Cost | Notes |
|----------|------|-------|
| **GPU (A100)** | ~2-5 AKT/day | $0.50-1.25/day |
| **Storage (100GB)** | ~0.1 AKT/day | Persistent volume |
| **LLM API** | ~$0.50-2.00/experiment | Claude/GPT-4 calls |
| **25 iterations** | ~$50-100 total | 2 hours runtime |

---

## 🎯 Expected Results

After 25 iterations:

- **Success rate**: ~60-70% of experiments improve performance
- **Typical improvement**: 8-15% reduction in validation BPB
- **Best discoveries**: Gradient clipping, LR scheduling, architecture tweaks
- **Artifacts**: `results.tsv` with full experiment log

---

## 🐦 Share Your Results

```bash
# Generate shareable content
cat SOCIAL_POST.md

# Create visualization
python visualize_results.py

# Show experiment log
cat results.tsv
```

---

## 🔧 Configuration Options

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_ITERS` | 25 | Number of experiments |
| `EXPERIMENT_TIMEOUT_SECONDS` | 900 | Training time limit (5 min) |
| `LLM_PROVIDER` | anthropic | LLM API provider |
| `MODEL_NAME` | claude-3-7-sonnet-20250219 | Model for experiments |
| `LLM_API_KEY` | (required) | Your API key |

---

## 🚨 Troubleshooting

**Container won't start:**
- Check GPU is available: `nvidia-smi`
- Verify environment variables are set

**Training crashes:**
- Check logs: `/data/logs/prepare.log`
- Reduce `EXPERIMENT_TIMEOUT_SECONDS` to 300

**No improvement:**
- Increase `MAX_ITERS` to 50-100
- Try different `MODEL_NAME` (GPT-4, Claude 3.5)

---

## 📚 Next Steps

1. **Customize**: Edit `train.py` with your own model
2. **Scale**: Deploy multiple instances on Akash
3. **Optimize**: Tune hyperparameters for your workload
4. **Share**: Post results on X with #AkashNetwork #AI

---

**Need help?** Check `DEPLOY.md` for detailed deployment instructions.

