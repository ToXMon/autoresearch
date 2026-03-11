# AutoResearch Safe Starter for Akash

![teaser](progress.png)

A beginner-friendly guide to running the [karpathy/autoresearch](https://github.com/karpathy/autoresearch) autonomous AI research loop on [Akash Network](https://akash.network/) using Docker.

---

## Table of contents

1. [What this project is](#1-what-this-project-is)
2. [What karpathy/autoresearch does](#2-what-karpathyautoresearch-does)
3. [What Akash does in this setup](#3-what-akash-does-in-this-setup)
4. [Why an LLM API key is required](#4-why-an-llm-api-key-is-required)
5. [Where the API key is entered](#5-where-the-api-key-is-entered)
6. [Why the key is not stored in the image](#6-why-the-key-is-not-stored-in-the-image)
7. [Project structure](#7-project-structure)
8. [Local development](#8-local-development)
9. [Building the Docker image](#9-building-the-docker-image)
10. [Pushing the image to a registry](#10-pushing-the-image-to-a-registry)
11. [Deploying on Akash Console](#11-deploying-on-akash-console)
12. [Where logs go](#12-where-logs-go)
13. [Where outputs go](#13-where-outputs-go)
14. [Common mistakes](#14-common-mistakes)
15. [Troubleshooting](#15-troubleshooting)
16. [Security notes](#16-security-notes)

---

## 1. What this project is

This repository is an **AutoResearch Safe Starter** — a Docker-based setup that makes it easy to deploy [karpathy/autoresearch](https://github.com/karpathy/autoresearch) on [Akash Network](https://akash.network/), a decentralized GPU cloud.

It is intentionally simple and beginner-friendly. You do not need to be an expert in Docker, Kubernetes, or decentralized infrastructure to use it. Everything you need to get started is in this guide.

> *"One day, frontier AI research used to be done by meat computers in between eating, sleeping, having other fun... This repo is the story of how it all began."* — @karpathy, March 2026

---

## 2. What karpathy/autoresearch does

**autoresearch** gives an AI coding agent a small, real neural-network training setup and tells it to improve the model autonomously — overnight, while you sleep.

Here is the loop:

1. The agent reads `program.md` (your instructions) and `train.py` (the training code).
2. It proposes a change — maybe a new optimizer, a different batch size, a tweaked architecture.
3. It edits `train.py` and runs training for exactly **5 minutes**.
4. It checks whether the model improved (lower **val_bpb** = better).
5. If the change helped, it keeps it. If not, it discards it and tries something else.
6. It repeats until you stop it.

You wake up to a log of experiments and, hopefully, a better model. You never touch the Python files yourself — instead you write `program.md` to guide the agent's strategy.

**Key files (from karpathy/autoresearch):**

| File | Role |
|---|---|
| `prepare.py` | Downloads training data and trains a tokenizer. **Do not modify.** |
| `train.py` | The full GPT model, optimizer, and training loop. **The agent edits this.** |
| `program.md` | Plain-text instructions for the agent. **You edit this.** |

The metric tracked is **val_bpb** (validation bits per byte). Lower is better, and it is vocabulary-size-independent so different architectures can be fairly compared.

---

## 3. What Akash does in this setup

[Akash Network](https://akash.network/) is a **decentralized cloud marketplace** where independent data-center operators (called "providers") rent out their GPU and CPU capacity. You pay in AKT (Akash's token) or USDC.

In this setup, Akash provides:

- A **GPU node** (NVIDIA H100, A100, etc.) to run training on.
- **Persistent storage** mounted at `/data` so your logs and model checkpoints survive container restarts.
- A **browser-based console** ([console.akash.network](https://console.akash.network/)) that lets you deploy without any command-line tools.

You describe your deployment in a file called `deploy.yaml` (an Akash SDL — Stack Definition Language file). Akash providers bid on your deployment, and you pick the one that fits your budget.

---

## 4. Why an LLM API key is required

The autonomous research loop requires an AI coding agent — something like Claude (Anthropic) or GPT-4 (OpenAI) — to read the training code, plan experiments, and write new code.

These AI services are not free. You need an **API key** to authenticate requests to them. Without a valid key, the agent cannot generate any code and the experiment loop cannot run.

**Where to get a key:**

| Provider | Where to get a key |
|---|---|
| Anthropic (Claude) | [console.anthropic.com](https://console.anthropic.com/) |
| OpenAI (GPT-4) | [platform.openai.com](https://platform.openai.com/api-keys) |

The key looks something like `sk-ant-api03-...` (Anthropic) or `sk-proj-...` (OpenAI). Keep it private — treat it like a password.

---

## 5. Where the API key is entered

**Short answer:** you pass it as an environment variable when you start the container. You never put it in any file that gets saved or committed to git.

There are two main ways to do this:

### Option A — Docker CLI (local testing)

```bash
docker run --gpus all \
  -e LLM_API_KEY=sk-ant-api03-your-real-key-here \
  -e LLM_PROVIDER=anthropic \
  -e MODEL_NAME=claude-3-7-sonnet-20250219 \
  -v /my/local/data:/data \
  ghcr.io/your-github-username/autoresearch:latest
```

Replace `sk-ant-api03-your-real-key-here` with your actual key. The `-e` flag sets an environment variable inside the container.

### Option B — Akash Console (cloud deployment)

When you deploy via [console.akash.network](https://console.akash.network/), the deploy form has an **environment variables** section where you can type your key directly into the browser. It is sent securely to the provider and never written to a file.

See [Section 11 — Deploying on Akash Console](#11-deploying-on-akash-console) for step-by-step instructions.

### All environment variables

The container reads the following variables at startup:

**Required (must be set):**

| Variable | Secret? | Example value | What it does |
|---|---|---|---|
| `LLM_API_KEY` | **Yes** | `sk-ant-api03-...` | API key for the LLM provider. Never commit this. |
| `LLM_PROVIDER` | No | `anthropic` | Name of the provider (`anthropic`, `openai`, etc.) |
| `MODEL_NAME` | No | `claude-3-7-sonnet-20250219` | The exact model identifier to use |

**Optional (safe defaults are built in):**

| Variable | Default | What it does |
|---|---|---|
| `DATA_DIR` | `/data` | Root directory for all persistent data |
| `LOG_DIR` | `/data/logs` | Where startup and run logs are written |
| `OUTPUT_DIR` | `/data/output` | Where model checkpoints are saved |
| `RUN_MODE` | `agent` | How the container runs (`agent` is the only supported mode) |
| `MAX_ITERS` | `25` | Maximum number of experiment iterations the agent may run |
| `EXPERIMENT_TIMEOUT_SECONDS` | `900` | Seconds before a single experiment is automatically cancelled |
| `LLM_API_BASE` | *(empty)* | Custom API endpoint URL — leave empty unless using a self-hosted model |

See [`.env.example`](.env.example) for a copy-paste template of all variables.

---

## 6. Why the key is not stored in the image

If your API key were baked into the Docker image, anyone who can pull the image from a registry could extract and use your key — and you would pay for their API calls.

This starter follows a simple rule: **secrets live outside the image, always**.

- The `Dockerfile` contains no secrets.
- The `start.sh` entrypoint script contains no secrets.
- The `deploy.yaml` SDL file contains only a placeholder (`REPLACE_WITH_YOUR_LLM_API_KEY_AT_DEPLOY_TIME`).

Your real key is passed in at container start time via an environment variable. It is read by `start.sh` only to confirm it is present (so the container fails fast with a clear error if you forgot to set it), and then it stays in memory for the coding agent to use later. It is never written to a file and never printed in full in the logs.

---

## 7. Project structure

```
autoresearch/
├── Dockerfile          # Builds the container image (no secrets inside)
├── start.sh            # Container entrypoint: validates config, prepares repo, waits for agent
├── deploy.yaml         # Akash SDL: describes hardware, storage, and env vars for deployment
├── .env.example        # Template of all environment variables (copy and fill in locally)
├── program.md          # Instructions for the AI agent (you edit this to guide experiments)
├── prepare.py          # One-time data prep: downloads training data and trains tokenizer
├── train.py            # GPT model + training loop (the agent edits this file)
├── pyproject.toml      # Python dependencies
├── CONTRIBUTING.md     # How to run locally and review agent PRs
└── README.md           # This file
```

**Key paths inside the running container:**

```
/app/autoresearch/   — the karpathy/autoresearch repo (baked in at build time)
/data/               — persistent volume root (mount a volume here on Akash)
/data/logs/          — log files written at runtime
/data/output/        — model checkpoints and experiment results
/start.sh            — the entrypoint script
```

---

## 8. Local development

Use this section if you want to run the project on your own machine (without Docker or Akash) to test changes before deploying.

**Requirements:**

- A single NVIDIA GPU (tested on H100; other cards may work)
- Python 3.10 or newer
- [uv](https://docs.astral.sh/uv/) — a fast Python package manager

```bash
# Step 1 — Install uv (skip if you already have it)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Step 2 — Install Python dependencies
uv sync

# Step 3 — Download training data and train the tokenizer (one-time, ~2 min)
uv run prepare.py

# Step 4 — Run one training experiment to make sure everything works (~5 min)
uv run train.py
```

If `uv run train.py` completes and prints a `val_bpb:` result, your local setup is working.

**Running the agent locally:**

Open `program.md` and read the instructions inside. Then attach your preferred coding agent (e.g. Claude in an IDE extension) to this repository, point it at `program.md`, and start it. The agent will run the experiment loop described in that file.

For PR review guidance and more development tips, see [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## 9. Building the Docker image

You only need to build the image if you want to deploy to Akash (or any other container platform). Local development does not require Docker.

**Prerequisites:** [Docker Desktop](https://www.docker.com/products/docker-desktop/) (or Docker Engine on Linux) installed and running.

```bash
# Clone this repository first if you haven't already
git clone https://github.com/ToXMon/autoresearch.git
cd autoresearch

# Build the image and tag it with your registry path
# Replace "your-github-username" with your actual GitHub username
docker build -t ghcr.io/your-github-username/autoresearch:latest .
```

The build downloads the CUDA base image and clones `karpathy/autoresearch` into the image. It takes a few minutes the first time (most of that is downloading the CUDA base layer).

**What the image contains after the build:**

| Layer | What it provides |
|---|---|
| `nvidia/cuda:12.4.1-runtime-ubuntu22.04` | CUDA runtime so PyTorch can use the GPU |
| System packages | `python3`, `git`, `curl`, `ca-certificates`, `tini`, `bash` |
| `uv` | Fast Python package manager |
| `/app/autoresearch` | A shallow clone of `karpathy/autoresearch` |
| `/data/logs`, `/data/output` | Empty directories for runtime outputs |
| `/start.sh` | Entrypoint script |

> The image does **not** contain your API key, any training data, or any model checkpoints. Those are created or injected at runtime.

---

## 10. Pushing the image to a registry

Akash providers pull your container image from a public registry when they start your deployment. You need to push your locally built image to a registry before deploying.

**GitHub Container Registry (recommended — free for public images):**

```bash
# Log in to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u your-github-username --password-stdin

# Push the image
docker push ghcr.io/your-github-username/autoresearch:latest
```

After pushing, make the image **public** in your GitHub package settings so that Akash providers can pull it without authentication:

1. Go to `github.com/your-github-username` → **Packages** tab.
2. Click the `autoresearch` package.
3. Click **Package settings** → **Change visibility** → **Public**.

**Docker Hub (alternative):**

```bash
docker login

docker tag ghcr.io/your-github-username/autoresearch:latest \
  your-dockerhub-username/autoresearch:latest

docker push your-dockerhub-username/autoresearch:latest
```

---

## 11. Deploying on Akash Console

[Akash Console](https://console.akash.network/) is a browser-based UI. You do not need any command-line Akash tools to deploy.

### Step 1 — Update deploy.yaml with your image

Open `deploy.yaml` in a text editor and replace the placeholder image name:

```yaml
# Before (placeholder)
image: your-registry/autoresearch:latest

# After (your real image)
image: ghcr.io/your-github-username/autoresearch:latest
```

### Step 2 — Connect your Akash wallet

1. Go to [console.akash.network](https://console.akash.network/).
2. Click **Connect Wallet** in the top right.
3. Follow the prompts to connect Keplr or another supported wallet with some AKT or USDC balance.

### Step 3 — Create a new deployment

1. Click **Deploy** in the left sidebar.
2. Select **Build your template** → **SDL**.
3. Paste the full contents of your updated `deploy.yaml` into the editor.

### Step 4 — Set your API key in the deploy form

Before submitting, look for the environment variables section in the form. Find `LLM_API_KEY` and replace the placeholder with your real key:

```
LLM_API_KEY=sk-ant-api03-your-real-key-here
```

> ⚠️ **Do not put a real key in `deploy.yaml` and commit it to git.** Always enter the key in the browser form so it is never saved to a file.

### Step 5 — Review bids and deploy

1. Click **Deploy** (or **Create Deployment**).
2. Wait for provider bids to appear — this usually takes 30–60 seconds.
3. Pick a provider with an NVIDIA GPU listed in its attributes.
4. Click **Accept Bid** → **Deploy**.

### Step 6 — Watch the startup logs

Once deployed, click your deployment → **Logs** tab. You should see something like:

```
==> AutoResearch Safe Starter
    APP_HOME   : /app
    DATA_DIR   : /data
    LOG_DIR    : /data/logs
    ...
    LLM_API_KEY  : [set]
==> Installing Python dependencies with uv...
==> Running prepare.py (downloads data and trains tokenizer)...
==> Agent mode is ready.
==> Keeping the container alive for later orchestration...
```

If you see `ERROR: LLM_API_KEY is not set`, the key was not passed correctly — see [Section 14 — Common mistakes](#14-common-mistakes).

---

## 12. Where logs go

| Log file | Path inside container | What it contains |
|---|---|---|
| Startup log | Akash Console → Logs tab | Everything printed by `start.sh` at container start |
| Data preparation log | `/data/logs/prepare.log` | Output of `prepare.py` (data download, tokenizer training) |
| Experiment run log | `/data/logs/run.log` *(created by agent)* | Training output, val_bpb results, errors |

**Reading a log file from Akash Console:**

Use the **Shell** tab in the Akash Console (if available), or use the `akash` CLI:

```bash
akash provider lease-shell \
  --from <your-wallet-address> \
  --dseq <deployment-sequence> \
  --provider <provider-address> \
  -- cat /data/logs/prepare.log
```

Because `/data` is a persistent volume, log files survive container restarts.

---

## 13. Where outputs go

| Output | Path inside container | What it is |
|---|---|---|
| Model checkpoints | `/data/output/` | Saved model weights from training runs |
| Experiment results | `/data/output/results.tsv` *(created by agent)* | Tab-separated table of val_bpb scores per experiment |
| All persistent data | `/data/` | Everything under this path survives restarts |

**Downloading outputs:**

Use the Akash Console Shell tab or the `akash` CLI to list files in the container:

```bash
akash provider lease-shell \
  --from <your-wallet-address> \
  --dseq <deployment-sequence> \
  --provider <provider-address> \
  -- ls /data/output/
```

> Without a persistent volume, outputs are lost when the container stops. Make sure the `data` volume is configured in your `deploy.yaml` (it is by default).

---

## 14. Common mistakes

### Forgetting to set `LLM_API_KEY`

The container will exit immediately with:
```
ERROR: LLM_API_KEY is not set.
```
Fix: add `-e LLM_API_KEY=your-key` to your Docker command, or enter it in the Akash Console deploy form.

### Committing the API key to git

If you paste your real key into `deploy.yaml` and commit it, it becomes part of your git history and visible to anyone with access to the repository.

Fix: use the placeholder in `deploy.yaml` and enter the real value only in the Akash Console form or a local `.env` file that is listed in `.gitignore`.

### Using a private Docker image

Akash providers cannot pull private images. If your image is private, the deployment will fail with an image pull error.

Fix: make the image public in your registry settings (see [Section 10](#10-pushing-the-image-to-a-registry)).

### Wrong image tag

If the tag in `deploy.yaml` does not match the tag you pushed, the pull will fail.

Fix: make sure the image name in `deploy.yaml` exactly matches what you pushed, including the tag (e.g. `:latest`).

### `beta3` storage class not available

Some Akash providers only support `beta2` persistent storage.

Fix: change `class: beta3` to `class: beta2` in the `storage:` section of `deploy.yaml`.

### No GPU bids

If no providers bid on your deployment, the GPU request may be too strict or the price too low.

Fix:
- Increase `pricing.amount` in `deploy.yaml` (try `50000` or higher).
- Remove the `signedBy:` filter to broaden provider selection.
- Check [Akash Console](https://console.akash.network/) for current GPU availability.

---

## 15. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `ERROR: LLM_API_KEY is not set` | Key not passed as env var | Set `LLM_API_KEY` in your Docker run command or Akash deploy form |
| `ERROR: Missing required environment variable: LLM_PROVIDER` | Provider not set | Add `LLM_PROVIDER=anthropic` (or your provider) to the env vars |
| `ERROR: Missing required environment variable: MODEL_NAME` | Model name not set | Add `MODEL_NAME=claude-3-7-sonnet-20250219` to the env vars |
| Container exits right away | Config error in `start.sh` | Check the Akash Console Logs tab for the exact error message |
| No bids after 2+ minutes | No matching provider | Raise `pricing.amount`, remove `signedBy`, or try a different region |
| Image pull fails | Private image or wrong tag | Make image public; verify the tag in `deploy.yaml` matches what you pushed |
| `beta3` storage not available | Provider limitation | Change `class: beta3` to `class: beta2` in `deploy.yaml` |
| `/data/logs/prepare.log` is empty | Volume not mounted correctly | Confirm the `params.storage.data.mount: /data` block is in `deploy.yaml` |
| Agent never starts experiments | Agent not attached | Connect your coding agent to the running container and point it at `program.md` |
| `uv sync` fails during startup | Network issue or cache miss | Redeploy; the image will retry on a fresh provider |

---

## 16. Security notes

- **Never put a real API key in `deploy.yaml`, `Dockerfile`, `start.sh`, or any other file in this repository.** Use environment variables injected at runtime only.
- **Never commit a `.env` file with real values.** The `.gitignore` in this repository already excludes `.env`, but always double-check with `git status` before committing.
- **Treat your API key like a password.** If you suspect it has been exposed, revoke it immediately at your provider's dashboard and generate a new one.
- **Use signed providers on Akash.** The `signedBy:` filter in `deploy.yaml` limits deployments to providers that have been verified by trusted Akash auditors. Remove it only if you trust the full pool of providers.
- **Keep the image public but secrets private.** A public Docker image is safe as long as no secrets are baked into it. Anyone can pull and inspect the image layers — which is fine because there is nothing sensitive in them.
- **Rotate keys periodically.** If you run long autonomous experiments, consider using short-lived API keys or keys with usage limits set on the provider dashboard.

---

## Design notes

- **Single file to modify.** The agent only touches `train.py`. This keeps the scope manageable and diffs reviewable.
- **Fixed time budget.** Training always runs for exactly 5 minutes, making experiments directly comparable regardless of what the agent changes. You can expect approximately 12 experiments per hour, or around 100 overnight.
- **Self-contained.** No external dependencies beyond PyTorch and a few small packages. One GPU, one file, one metric.

## Platform support

This project requires a single NVIDIA GPU. For running on other platforms (macOS, Windows, smaller GPUs), see these community forks:

- [miolini/autoresearch-macos](https://github.com/miolini/autoresearch-macos) (macOS)
- [trevin-creator/autoresearch-mlx](https://github.com/trevin-creator/autoresearch-mlx) (macOS)
- [jsegov/autoresearch-win-rtx](https://github.com/jsegov/autoresearch-win-rtx) (Windows)

For tips on tuning for smaller hardware, see the [upstream karpathy/autoresearch README](https://github.com/karpathy/autoresearch#platform-support).

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for how to run the project locally and how to review agent-generated pull requests.

## License

MIT
