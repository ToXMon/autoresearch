# Deploying AutoResearch to Akash Network

This guide walks you through deploying the autonomous AI research agent to Akash Network using Akash Console.

## Prerequisites

1. **Akash Account**: Create an account at [console.akash.network](https://console.akash.network)
2. **AKT Tokens**: You need AKT or USDC for deployment costs. Get AKT from:
   - [Coinbase](https://www.coinbase.com)
   - [Kraken](https://www.kraken.com)
   - [Osmosis DEX](https://app.osmosis.zone)
3. **LLM API Key**: An API key from your preferred LLM provider:
   - **Anthropic** (recommended): [console.anthropic.com](https://console.anthropic.com)
   - **OpenAI**: [platform.openai.com](https://platform.openai.com)
   - **Other providers**: Any OpenAI-compatible API

## Step 1: Build and Push Docker Image

The autonomous agent runs in a container. Build and push it to a container registry.

### Option A: GitHub Container Registry (Recommended)

```bash
# Navigate to the project directory
cd autoresearch

# Build the image (replace YOUR_USERNAME)
docker build -t ghcr.io/YOUR_USERNAME/autoresearch-agent:v1 .

# Login to GitHub Container Registry
echo $GITHUB_TOKEN | docker login ghcr.io -u YOUR_USERNAME --password-stdin

# Push the image
docker push ghcr.io/YOUR_USERNAME/autoresearch-agent:v1
```

### Option B: Docker Hub

```bash
# Build the image
docker build -t YOUR_USERNAME/autoresearch-agent:v1 .

# Login to Docker Hub
docker login

# Push the image
docker push YOUR_USERNAME/autoresearch-agent:v1
```

## Step 2: Update deploy.yaml

Edit `deploy.yaml` to reference your pushed image:

```yaml
services:
  autoresearch:
    # Replace with your actual image reference
    image: ghcr.io/YOUR_USERNAME/autoresearch-agent:v1
```

## Step 3: Deploy via Akash Console

1. **Open Akash Console**: Go to [console.akash.network](https://console.akash.network)

2. **Connect Wallet**: Click "Connect Wallet" and select your preferred wallet (Keplr, Leap, etc.)

3. **Create Deployment**:
   - Click "Create Deployment" in the sidebar
   - Select "Empty" or "Custom" SDL option
   - Paste the contents of your `deploy.yaml` file

4. **Configure Environment Variables**:
   
   Update these critical values in the SDL:
   
   ```yaml
   env:
     # Your LLM provider (anthropic, openai, etc.)
     - LLM_PROVIDER=anthropic
     
     # Model to use for generating experiments
     - MODEL_NAME=claude-3-7-sonnet-20250219
     
     # YOUR ACTUAL API KEY - this is REQUIRED
     - LLM_API_KEY=sk-ant-api03-YOUR-KEY-HERE
     
     # Number of experiment iterations (default: 25)
     - MAX_ITERS=100
     
     # Timeout per experiment in seconds (default: 900 = 15 min)
     - EXPERIMENT_TIMEOUT_SECONDS=900
   ```

5. **Set Pricing**: Review the pricing configuration:
   - Default: 10,000 uakt per block (~0.01 AKT)
   - Adjust higher for better provider availability

6. **Choose Provider**: 
   - Review available providers
   - Select one with NVIDIA GPU support
   - Consider provider reputation and location

7. **Deploy**: Click "Deploy" and confirm the transaction in your wallet

## Step 4: Monitor the Deployment

Once deployed:

1. **View Logs**: In Akash Console, click on your deployment and select "Logs"
   - Watch for the autonomous agent starting
   - Each experiment iteration will be logged

2. **Check Results**: Results are stored in the persistent volume at `/data/logs/results.tsv`
   - You can view this via the shell access in Akash Console

3. **Monitor Progress**: The agent will:
   - Run baseline training (first iteration)
   - Generate experiments using the LLM
   - Track improvements in `val_bpb`
   - Keep successful experiments, revert failed ones

## Environment Variables Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `LLM_API_KEY` | **Yes** | - | Your LLM provider API key |
| `LLM_PROVIDER` | **Yes** | - | Provider name: `anthropic`, `openai`, etc. |
| `MODEL_NAME` | **Yes** | - | Model ID to use (e.g., `claude-3-7-sonnet-20250219`) |
| `LLM_API_BASE` | No | - | Custom API endpoint (leave empty for default) |
| `MAX_ITERS` | No | 25 | Number of experiment iterations |
| `EXPERIMENT_TIMEOUT_SECONDS` | No | 900 | Timeout per training run |
| `RUN_MODE` | No | agent | `agent` or `prepare-only` |

## Cost Estimation

- **GPU (A100)**: ~2-5 AKT/day depending on provider
- **Storage (100GB persistent)**: ~0.1 AKT/day
- **LLM API calls**: ~$0.50-2.00 per experiment (depends on model)
- **Total for 100 iterations**: ~10-20 AKT + ~$50-200 in LLM costs

## Troubleshooting

### Container won't start
- Verify `LLM_API_KEY` is set correctly
- Check that `LLM_PROVIDER` matches your API key type
- Ensure image reference is correct and accessible

### Training fails immediately
- Check logs for CUDA errors
- Verify GPU is available (provider may have GPU issues)
- Data preparation should complete before training starts

### Agent not making progress
- Check LLM API key is valid
- Verify model name is correct
- Look for API rate limiting in logs

## Stopping the Deployment

When you're done:

1. Go to your deployment in Akash Console
2. Click "Close Deployment"
3. Confirm the transaction

**Note**: Persistent storage will be retained for a period, but download any important results before closing.

## Advanced: Using Different LLM Providers

### OpenAI
```yaml
- LLM_PROVIDER=openai
- MODEL_NAME=gpt-4
- LLM_API_KEY=sk-YOUR-OPENAI-KEY
```

### Custom OpenAI-Compatible API (e.g., Together, Anyscale)
```yaml
- LLM_PROVIDER=openai
- MODEL_NAME=meta-llama/Llama-3-70b-chat-hf
- LLM_API_KEY=YOUR_API_KEY
- LLM_API_BASE=https://api.together.xyz/v1
```

### Self-Hosted LLM (vLLM, Ollama)
```yaml
- LLM_PROVIDER=openai
- MODEL_NAME=local-model
- LLM_API_KEY=dummy
- LLM_API_BASE=http://your-llm-server:8000/v1
```
