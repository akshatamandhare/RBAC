# Contributing

## Setup
1. Create virtual environment
2. Install dependencies with pip install -r requirements.txt
3. Run tests with python -m pytest -q

## Pull Request Checklist
- Add or update tests for new functionality
- Keep RBAC and auth behavior backward compatible
- Update docs in docs/ when endpoints or behavior change
- Verify benchmark script runs

## Coding Guidelines
- Keep API models explicit and validated
- Avoid storing secrets in code
- Prefer deterministic tests and mock provider for LLM paths
