# uv Quick Reference

uv is a fast Python package manager that replaces pip, venv, and pip-tools. Full documentation: https://docs.astral.sh/uv/

## Key Concepts

### Lock Files (`uv.lock`)

- Contains exact versions of ALL packages (direct + transitive)
- Ensures everyone gets identical dependencies
- **Always commit** `uv.lock` with `pyproject.toml`
- Never edit manually - regenerate with `uv lock`

### Dependency Groups

```toml
# pyproject.toml

[project]
dependencies = [
    "requests>=2.31.0",   # Runtime (production)
]

[dependency-groups]
dev = [
    "pytest>=8.0.0",      # Development only
]
```

- **Runtime**: `uv sync` (production)
- **Dev**: `uv sync --group dev` (development)

## Common Commands

```bash
# Add dependencies
uv add requests              # Runtime
uv add --dev pytest          # Development

# Remove dependencies
uv remove requests

# Update packages
uv lock --upgrade-package requests   # Specific package
uv lock --upgrade                    # All packages

# Install from lock file
uv sync --group dev

# Run code (uses correct venv automatically)
uv run python script.py
uv run pytest tests

# Run tools without installing
uvx ruff format
uvx mypy src/
```

## uv vs pip

| pip | uv |
|-----|-----|
| `pip install requests` | `uv add requests` |
| `pip uninstall requests` | `uv remove requests` |
| `pip freeze > requirements.txt` | Automatic (`uv.lock`) |
| `source .venv/bin/activate` | Not needed |
| `python script.py` | `uv run python script.py` |

**Key difference**: uv manages venvs automatically. No activation needed.

## Version Constraints

```bash
uv add "requests>=2.31.0"      # Minimum version (recommended)
uv add "django==4.2.0"         # Exact version (use sparingly)
uv add "numpy>=1.24,<2.0"      # Version range
```

## Best Practices

1. **Use `uv add`**, don't edit pyproject.toml manually
2. **Always commit both** `pyproject.toml` and `uv.lock`
3. **Run `uv sync --group dev`** after `git pull`
4. **Use `uvx`** for tools (ruff, mypy), `uv add --dev` for test libraries
5. **Don't mix with pip** - let uv manage everything
