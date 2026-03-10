# Contributing

Thanks for helping improve this repository.

## Run locally

This project uses `uv` to manage dependencies.

```bash
# Install dependencies
uv sync

# Prepare data and tokenizer once
uv run prepare.py

# Run one training experiment
uv run train.py
```

If you are setting up the project for the first time, read the quick start in [`README.md`](README.md) first.

## Review agent PRs

When reviewing an agent-generated PR:

1. Read the PR summary and changed files first.
2. Check that the changes are small, focused, and easy to understand.
3. Confirm the docs stay beginner-friendly and explain any new behavior clearly.
4. Verify that no secrets, tokens, or private paths were hardcoded.
5. Confirm any commands, scripts, or storage paths match the repository guidance.

## Give feedback through PR comments

Please leave feedback directly on the pull request:

- Use **line comments** for specific code or doc issues.
- Use the **main PR conversation** for higher-level feedback or follow-up questions.
- Be explicit about the change you want so the next agent can address it in a small follow-up PR.
