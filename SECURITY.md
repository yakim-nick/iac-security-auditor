# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| latest  | :white_check_mark: |

## Reporting a Vulnerability

This project is a reference/template project. Security issues should still be
taken seriously. If you believe you have found a security vulnerability:

- **Do not** open a public issue describing it.
- Report it privately by email or through GitHub's Security Advisories
  ("Report a vulnerability") flow on this repository.
- Include a description of the issue, how to reproduce it, and the affected
  version.

You will receive a response within 5 business days, and we will coordinate a
fix before disclosing details publicly.

## Security considerations

- The project runs LLM-based agents and may parse untrusted input (IaC
  manifests, prompts, etc.). Treat agent output as untrusted.
- Never commit real credentials, API keys, or tokens. Use environment
  variables or a secret manager.
- Review the `.github/workflows` and `k8s/` manifests for secret handling
  before deploying to a shared environment.
