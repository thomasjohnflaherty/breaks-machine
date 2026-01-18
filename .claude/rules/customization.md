# Customization Guide

## Adding VSCode Extensions

### Current Extensions

This template includes:
- `ms-python.python` - Python language support
- `ms-toolsai.jupyter` - Jupyter notebook support

### Adding More Extensions

**Edit** `.devcontainer/devcontainer.json`:

```json
{
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-toolsai.jupyter",
        "ms-python.vscode-pylance",
        "charliermarsh.ruff"
      ]
    }
  }
}
```

**Finding extension IDs**: Open VSCode → Extensions sidebar → Click extension → Copy ID

**After adding**: Rebuild container (Command Palette → "Dev Containers: Rebuild Container")

### Recommended Extensions

```json
"ms-python.vscode-pylance",     // Enhanced Python language server
"charliermarsh.ruff",           // Ruff extension (formatting/linting)
"eamodio.gitlens",              // Git supercharged
"usernamehw.errorlens",         // Inline error display
```

## Adding Devcontainer Features

### Current Features

- `ghcr.io/jsburckhardt/devcontainer-features/uv:1` - uv package manager
- `ghcr.io/jsburckhardt/devcontainer-features/ruff:1` - ruff linter/formatter

### Adding Features

Browse available features at: https://containers.dev/features

**Edit** `.devcontainer/devcontainer.json`:

```json
{
  "features": {
    "ghcr.io/jsburckhardt/devcontainer-features/uv:1": {},
    "ghcr.io/jsburckhardt/devcontainer-features/ruff:1": {},
    "ghcr.io/devcontainers/features/node:1": {
      "version": "20"
    },
    "ghcr.io/devcontainers/features/docker-in-docker:2": {}
  }
}
```

**After adding**: Rebuild container

## Changing Python Version

See detailed guide: @.claude/rules/version-management.md

**Quick reference** - update all four files:

1. `.python-version` → `3.14`
2. `.devcontainer/devcontainer.json` → `python:3.14`
3. `pyproject.toml` → `requires-python = ">=3.14"`
4. `Dockerfile` → `FROM python:3.14-slim`
5. Rebuild container, run `uv lock --upgrade`, test and commit

## Configuring Ruff

**Add to** `pyproject.toml`:

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
exclude = [".venv", "__pycache__"]

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort (import sorting)
    "UP",  # pyupgrade
    "B",   # flake8-bugbear
]
ignore = ["E501"]  # Line too long (handled by formatter)

[tool.ruff.lint.isort]
known-first-party = ["example_project"]

[tool.ruff.lint.per-file-ignores]
"tests/**/*.py" = ["S101"]  # Allow assert in tests
```

See full options: https://docs.astral.sh/ruff/configuration/

## Configuring pytest

**Add to** `pyproject.toml`:

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
addopts = ["-v", "--tb=short", "--strict-markers"]

# Optional: define custom markers
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]
```

Usage:
```bash
uv run pytest tests -m "not slow"
uv run pytest tests -m integration
```

## Adding System Packages

For quick installs via postCreateCommand:

```json
{
  "postCreateCommand": "sudo apt-get update && sudo apt-get install -y vim && uv sync --group dev"
}
```

For more complex setups, create `.devcontainer/Dockerfile`:

```dockerfile
FROM mcr.microsoft.com/devcontainers/python:3.13

RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*
```

Then update `.devcontainer/devcontainer.json`:

```json
{
  "build": {
    "dockerfile": "Dockerfile"
  }
}
```

## Best Practices

1. **Always rebuild after config changes**: Changes to `devcontainer.json` require container rebuild
2. **Use features over Dockerfile when possible**: Features are maintained and more portable
3. **Test in clean container**: After major changes, rebuild without cache to ensure reproducibility
4. **Version control devcontainer config**: Always commit `.devcontainer/` directory
5. **Keep it team-friendly**: Don't add personal preferences that affect the whole team
