# Contributing to iac-security-auditor

Thanks for contributing! This project audits Terraform/Kubernetes manifests
with parallel LLM agents, so keep prompt/agent behavior and secret handling in
mind when you change things.

## Getting started

```sh
make install     # install dev + runtime dependencies
make dev         # run the worker/API stack locally (see Makefile targets)
```

## Before you open a PR

- Run the test suite: `make test` (or `pytest`).
- Run the linter and formatter: `make lint` (ruff check) and `make format`
  (ruff format). Keep `pre-commit` passing: `pre-commit run --all-files`.
- Never commit real API keys, tokens, or credentials — use environment
  variables or a secret manager.
- If you change the rulesets or agent prompts, add/adjust tests that pin the
  expected behavior.

## Commits

Use conventional-commits style, e.g. `feat(rules): ...`, `fix(agents): ...`,
`docs(security): ...`.

## Reaching out

Open an issue to discuss bugs, feature ideas, or large changes before
submitting a PR.
