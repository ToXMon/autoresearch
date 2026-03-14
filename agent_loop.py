#!/usr/bin/env python3
"""
Autonomous Research Agent Loop

Implements the autoresearch experiment loop from program.md.
Runs inside the container, uses LLM to propose experiments,
executes training, and tracks results.
"""

import os
import sys
import json
import subprocess
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, Tuple

# Try to import litellm, fallback to direct API calls
try:
    import litellm
    HAS_LITELLM = True
except ImportError:
    HAS_LITELLM = False
    import urllib.request
    import urllib.error

# Configuration from environment
REPO_DIR = Path(os.environ.get("REPO_DIR", "/app/autoresearch"))
LOG_DIR = Path(os.environ.get("LOG_DIR", "/data/logs"))
OUTPUT_DIR = Path(os.environ.get("OUTPUT_DIR", "/data/output"))
MAX_ITERS = int(os.environ.get("MAX_ITERS", "25"))
EXPERIMENT_TIMEOUT = int(os.environ.get("EXPERIMENT_TIMEOUT_SECONDS", "900"))
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4")
LLM_API_KEY = os.environ.get("LLM_API_KEY", "")
LLM_BASE_URL = os.environ.get("LLM_BASE_URL", "")

class Colors:
    """Terminal colors for pretty output"""
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def log(msg: str, level: str = "INFO"):
    """Print timestamped log message"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    color = {
        "INFO": Colors.BLUE,
        "SUCCESS": Colors.GREEN,
        "WARNING": Colors.YELLOW,
        "ERROR": Colors.RED,
        "HEADER": Colors.HEADER
    }.get(level, "")
    print(f"{color}[{timestamp}] [{level}] {msg}{Colors.ENDC}")

def run_command(cmd: list, timeout: Optional[int] = None, cwd: Optional[Path] = None) -> Tuple[int, str, str]:
    """Run a command with optional timeout"""
    try:
        result = subprocess.run(
            cmd,
            cwd=cwd or REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "Command timed out"
    except Exception as e:
        return -1, "", str(e)

def get_git_state() -> Dict[str, str]:
    """Get current git branch and commit"""
    _, branch, _ = run_command(["git", "rev-parse", "--abbrev-ref", "HEAD"])
    _, commit, _ = run_command(["git", "rev-parse", "--short", "HEAD"])
    return {
        "branch": branch.strip(),
        "commit": commit.strip()
    }

def git_commit(message: str) -> bool:
    """Stage and commit changes to train.py"""
    run_command(["git", "add", "train.py"])
    code, _, err = run_command(["git", "commit", "-m", message])
    return code == 0

def git_reset_hard(commit: str = "HEAD~1") -> bool:
    """Reset to previous commit"""
    code, _, _ = run_command(["git", "reset", "--hard", commit])
    return code == 0

def read_file(path: Path) -> str:
    """Read file contents"""
    try:
        return path.read_text()
    except Exception as e:
        log(f"Failed to read {path}: {e}", "ERROR")
        return ""

def write_file(path: Path, content: str) -> bool:
    """Write content to file"""
    try:
        path.write_text(content)
        return True
    except Exception as e:
        log(f"Failed to write {path}: {e}", "ERROR")
        return False

def read_results_tsv() -> list:
    """Read existing results"""
    results_file = OUTPUT_DIR / "results.tsv"
    if not results_file.exists():
        return []
    lines = results_file.read_text().strip().split("\n")
    return [line for line in lines if line and not line.startswith("commit")]

def append_result(commit: str, val_bpb: float, memory_gb: float, status: str, description: str):
    """Append result to results.tsv"""
    results_file = OUTPUT_DIR / "results.tsv"
    header = "commit\tval_bpb\tmemory_gb\tstatus\tdescription"
    
    # Create file with header if needed
    if not results_file.exists():
        results_file.write_text(header + "\n")
    
    # Append result
    line = f"{commit}\t{val_bpb:.6f}\t{memory_gb:.1f}\t{status}\t{description}"
    with open(results_file, "a") as f:
        f.write(line + "\n")
    
    log(f"Logged result: {status} - val_bpb={val_bpb:.6f}", "SUCCESS")

def parse_training_output(output: str) -> Dict[str, Any]:
    """Parse training output for metrics"""
    metrics = {
        "val_bpb": None,
        "peak_vram_mb": None,
        "training_seconds": None,
        "crashed": False
    }
    
    # Look for val_bpb
    match = re.search(r"^val_bpb:\s*([\d.]+)", output, re.MULTILINE)
    if match:
        metrics["val_bpb"] = float(match.group(1))
    
    # Look for peak_vram_mb
    match = re.search(r"^peak_vram_mb:\s*([\d.]+)", output, re.MULTILINE)
    if match:
        metrics["peak_vram_mb"] = float(match.group(1))
    
    # Look for training_seconds
    match = re.search(r"^training_seconds:\s*([\d.]+)", output, re.MULTILINE)
    if match:
        metrics["training_seconds"] = float(match.group(1))
    
    # Check for crash indicators
    if metrics["val_bpb"] is None:
        metrics["crashed"] = True
    
    return metrics

def run_training() -> Dict[str, Any]:
    """Run training with timeout and capture output"""
    log(f"Running training (timeout: {EXPERIMENT_TIMEOUT}s)...", "INFO")
    
    start_time = time.time()
    
    try:
        result = subprocess.run(
            ["uv", "run", "train.py"],
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=EXPERIMENT_TIMEOUT
        )
        output = result.stdout + "\n" + result.stderr
        elapsed = time.time() - start_time
        
        log(f"Training completed in {elapsed:.1f}s", "SUCCESS")
        
        # Save full output to log file
        log_file = LOG_DIR / f"run_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        log_file.write_text(output)
        log(f"Full output saved to {log_file}", "INFO")
        
        return parse_training_output(output)
        
    except subprocess.TimeoutExpired:
        log(f"Training timed out after {EXPERIMENT_TIMEOUT}s", "WARNING")
        return {"val_bpb": None, "peak_vram_mb": None, "crashed": True}
    except Exception as e:
        log(f"Training failed: {e}", "ERROR")
        return {"val_bpb": None, "peak_vram_mb": None, "crashed": True}

def call_llm_direct(prompt: str) -> str:
    """Call LLM API directly without litellm"""
    provider = LLM_PROVIDER.lower()
    
    if provider == "anthropic":
        url = LLM_BASE_URL or "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": LLM_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        data = {
            "model": MODEL_NAME,
            "max_tokens": 8192,
            "messages": [{"role": "user", "content": prompt}]
        }
    elif provider == "zhipu" or provider == "z.ai":
        # Zhipu AI (Z.AI) - OpenAI-compatible API
        url = LLM_BASE_URL or "https://api.z.ai/api/coding/paas/v4/chat/completions"
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192
        }
    else:  # OpenAI-compatible
        url = LLM_BASE_URL or "https://api.openai.com/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {LLM_API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "model": MODEL_NAME,
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 8192
        }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers=headers,
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=120) as response:
            result = json.loads(response.read().decode())
            
            if provider == "anthropic":
                return result["content"][0]["text"]
            else:
                return result["choices"][0]["message"]["content"]
    except Exception as e:
        log(f"LLM API call failed: {e}", "ERROR")
        return ""

def call_llm_litellm(prompt: str) -> str:
    """Call LLM using litellm library"""
    provider = LLM_PROVIDER.lower()
    
    # Map provider to litellm model prefix
    if provider == "anthropic":
        model = f"anthropic/{MODEL_NAME}"
    elif provider == "openai":
        model = MODEL_NAME
    else:
        model = f"{provider}/{MODEL_NAME}"
    
    # Set api_base for zhipu provider if not explicitly set
    api_base = LLM_BASE_URL
    if provider in ["zhipu", "z.ai"] and not LLM_BASE_URL:
        api_base = "https://api.z.ai/api/coding/paas/v4/"

    try:
        response = litellm.completion(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=8192,
            api_key=LLM_API_KEY,
            api_base=api_base if api_base else None
        )
        return response.choices[0].message.content
    except Exception as e:
        log(f"LiteLLM call failed: {e}", "ERROR")
        return ""

def call_llm(prompt: str) -> str:
    """Call LLM with available method"""
    if HAS_LITELLM:
        return call_llm_litellm(prompt)
    else:
        return call_llm_direct(prompt)



def extract_code_from_response(response: str) -> Tuple[str, bool]:
    """Extract code from LLM response with robust handling.

    Returns: (code, is_valid)
    """
    # Pattern 1: Code blocks with python specifier
    python_blocks = re.findall(r"```python\n(.+?)```", response, re.DOTALL)

    # Pattern 2: Code blocks without language specifier
    plain_blocks = re.findall(r"```\n(.+?)```", response, re.DOTALL)

    # Pattern 3: Code blocks that might have whitespace before/after
    all_blocks = re.findall(r"```(?:python)?\s*\n(.+?)```", response, re.DOTALL)

    # Combine all found blocks and take the longest one
    all_found = python_blocks + plain_blocks + all_blocks

    if not all_found:
        log("No code blocks found in response", "ERROR")
        return "", False

    # Take the longest code block (most likely to be complete)
    code = max(all_found, key=len).strip()

    # Validate the code is complete
    is_valid = validate_extracted_code(code)

    if not is_valid:
        log(f"Extracted code failed validation (length: {len(code)})", "WARNING")

    return code, is_valid

def validate_extracted_code(code: str) -> bool:
    """Validate that extracted code is complete and contains required elements.

    Returns: True if code appears complete and valid
    """
    if len(code) < 10000:
        log(f"Code too short: {len(code)} chars (expected > 10000)", "WARNING")
        return False

    # Check for required elements that should be in train.py
    required_elements = [
        (r'class\s+GPT', 'class GPT'),
        (r'def\s+forward', 'def forward'),
        (r'import\s+torch', 'import torch'),
    ]

    missing = []
    for pattern, name in required_elements:
        if not re.search(pattern, code):
            missing.append(name)

    if missing:
        log(f"Code missing required elements: {missing}", "WARNING")
        return False

    # Check for balanced braces/brackets (basic syntax check)
    open_braces = code.count('{')
    close_braces = code.count('}')
    open_brackets = code.count('[')
    close_brackets = code.count(']')
    open_parens = code.count('(')
    close_parens = code.count(')')

    if open_braces != close_braces:
        log(f"Unbalanced braces: {{ = {open_braces}, }} = {close_braces}", "WARNING")
        return False
    if open_brackets != close_brackets:
        log(f"Unbalanced brackets: [ = {open_brackets}, ] = {close_brackets}", "WARNING")
        return False
    if open_parens != close_parens:
        log(f"Unbalanced parentheses: ( = {open_parens}, ) = {close_parens}", "WARNING")
        return False

    # Check that code doesn't end mid-line (truncation indicator)
    last_line = code.strip().split('\\n')[-1] if code.strip() else ''
    if last_line and not last_line.endswith(('}', ')', '"', "'", '`', ':', ',')):
        # Allow lines ending with common characters
        if not re.search(r'[a-zA-Z0-9_\s]$', last_line):
            log(f"Code may be truncated - ends unexpectedly: {last_line[-50:]}", "WARNING")
            return False

    log(f"Code validation passed: {len(code)} chars", "SUCCESS")
    return True

def generate_experiment(train_code: str, results_history: list, best_bpb: float) -> Tuple[str, str]:
    """Use LLM to generate next experiment"""
    
    # Build context from recent results
    recent_results = results_history[-10:] if len(results_history) > 10 else results_history
    results_context = "\n".join(recent_results) if recent_results else "No previous results (this is the baseline run)"
    
    prompt = f"""You are an autonomous AI researcher optimizing a GPT-style language model for pretraining.
Your goal is to achieve the LOWEST val_bpb (validation bits per byte) possible.
You have a FIXED time budget of 5 minutes per training run.

CURRENT BEST val_bpb: {best_bpb:.6f}

RECENT EXPERIMENT RESULTS:
{results_context}

CURRENT train.py CODE:
```python
{train_code}
```

RULES:
1. You can ONLY modify train.py - do not touch prepare.py
2. You can change: architecture, optimizer, hyperparameters, batch size, model size, etc.
3. The code MUST run without crashing
4. VRAM increase is acceptable for meaningful gains, but don't explode it
5. Simpler is better - don't add complexity for tiny gains
6. Each run is exactly 5 minutes of training time

Based on the results, propose ONE specific experimental change to train.py.
Output your response in this EXACT format:

DESCRIPTION: <one-line description of what you're trying>
REASONING: <why this might improve val_bpb>
CODE:
```python
<complete modified train.py>
```

Think carefully about what changes are most likely to improve val_bpb based on the experiment history.
If previous experiments show a pattern, exploit it. If stuck, try something different.
"""
    
    log("Calling LLM to generate experiment...", "INFO")
    response = call_llm(prompt)
    
    if not response:
        log("LLM returned empty response", "ERROR")
        return "", ""
    
    # Parse response
    desc_match = re.search(r"DESCRIPTION:\s*(.+?)(?:\n|$)", response)
    code_match = re.search(r"```python\n(.+?)```", response, re.DOTALL)
    
    description = desc_match.group(1).strip() if desc_match else "LLM experiment"
    code = code_match.group(1).strip() if code_match else ""
    
    if not code:
        log("Failed to extract code from LLM response", "ERROR")
        log(f"Full response: {response[:500]}...", "WARNING")
        return "", ""
    
    return description, code

def get_best_bpb(results: list) -> float:
    """Get best (lowest) val_bpb from results"""
    best = float('inf')
    for line in results:
        parts = line.split("\t")
        if len(parts) >= 2:
            try:
                bpb = float(parts[1])
                if bpb > 0:
                    best = min(best, bpb)
            except:
                pass
    return best if best != float('inf') else 999.999

def main():
    """Main experiment loop"""
    log("="*60, "HEADER")
    log("AutoResearch Autonomous Agent Loop", "HEADER")
    log("="*60, "HEADER")
    log(f"REPO_DIR: {REPO_DIR}", "INFO")
    log(f"MAX_ITERS: {MAX_ITERS}", "INFO")
    log(f"TIMEOUT: {EXPERIMENT_TIMEOUT}s", "INFO")
    log(f"LLM_PROVIDER: {LLM_PROVIDER}", "INFO")
    log(f"MODEL_NAME: {MODEL_NAME}", "INFO")
    log(f"HAS_LITELLM: {HAS_LITELLM}", "INFO")
    
    # Ensure directories exist
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Check for train.py
    train_path = REPO_DIR / "train.py"
    if not train_path.exists():
        log(f"train.py not found at {train_path}", "ERROR")
        sys.exit(1)
    
    # Get initial git state
    git_state = get_git_state()
    log(f"Starting on branch: {git_state['branch']}", "INFO")
    log(f"Initial commit: {git_state['commit']}", "INFO")
    
    # Load existing results
    results = read_results_tsv()
    best_bpb = get_best_bpb(results)
    log(f"Previous experiments: {len(results)}", "INFO")
    log(f"Best val_bpb so far: {best_bpb:.6f}", "INFO")
    
    # Main loop
    iteration = 0
    while iteration < MAX_ITERS:
        iteration += 1
        log("="*60, "HEADER")
        log(f"ITERATION {iteration}/{MAX_ITERS}", "HEADER")
        log("="*60, "HEADER")
        
        # Read current train.py
        train_code = read_file(train_path)
        if not train_code:
            log("Failed to read train.py", "ERROR")
            break
        
        # Generate experiment
        description, new_code = generate_experiment(train_code, results, best_bpb)
        
        if not new_code:
            log("Failed to generate experiment, retrying...", "WARNING")
            time.sleep(5)
            continue
        
        log(f"Experiment: {description}", "INFO")
        
        # Write new code
        if not write_file(train_path, new_code):
            log("Failed to write new code", "ERROR")
            continue
        
        # Commit
        if not git_commit(f"experiment: {description}"):
            log("Git commit failed (maybe no changes?)", "WARNING")
        
        # Get new commit hash
        git_state = get_git_state()
        commit = git_state["commit"]
        
        # Run training
        metrics = run_training()
        
        # Determine outcome
        if metrics["crashed"]:
            status = "crash"
            val_bpb = 0.0
            memory_gb = 0.0
            log("Experiment crashed!", "ERROR")
            
            # Revert
            git_reset_hard("HEAD~1")
            log("Reverted to previous commit", "WARNING")
        else:
            val_bpb = metrics["val_bpb"]
            memory_gb = (metrics["peak_vram_mb"] or 0) / 1024
            
            if val_bpb < best_bpb:
                status = "keep"
                best_bpb = val_bpb
                log(f"IMPROVEMENT! New best val_bpb: {best_bpb:.6f}", "SUCCESS")
            else:
                status = "discard"
                log(f"No improvement (val_bpb: {val_bpb:.6f} vs best: {best_bpb:.6f})", "WARNING")
                
                # Revert
                git_reset_hard("HEAD~1")
                log("Reverted to previous commit", "WARNING")
        
        # Log result
        append_result(commit, val_bpb, memory_gb, status, description)
        results.append(f"{commit}\t{val_bpb:.6f}\t{memory_gb:.1f}\t{status}\t{description}")
        
        # Brief pause between experiments
        time.sleep(2)
    
    log("="*60, "HEADER")
    log(f"EXPERIMENT LOOP COMPLETE ({iteration} iterations)", "HEADER")
    log(f"Final best val_bpb: {best_bpb:.6f}", "SUCCESS")
    log("="*60, "HEADER")

if __name__ == "__main__":
    main()
