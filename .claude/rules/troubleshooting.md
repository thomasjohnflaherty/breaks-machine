# Troubleshooting Guide

## Container Issues

### Container Fails to Build

**Common causes**:
1. **Network issues**: Check internet connection, try `docker pull mcr.microsoft.com/devcontainers/python:3.13`
2. **Insufficient disk space**: Run `docker system prune -a` to clean up
3. **Docker not running**: Open Docker Desktop (macOS/Windows) or `sudo systemctl start docker` (Linux)
4. **Corrupted cache**: Command Palette → "Dev Containers: Rebuild Container Without Cache"

### Container Builds But Won't Start

1. Check logs: VSCode → Output panel → "Dev Containers"
2. Manually run sync inside container: `uv sync --group dev`
3. Validate pyproject.toml: `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"`

### Container is Very Slow

**macOS file performance** - add to `.devcontainer/devcontainer.json`:
```json
"mounts": [
  "source=${localWorkspaceFolder},target=/workspace,type=bind,consistency=cached"
]
```

**Resource allocation**: Docker Desktop → Settings → Resources → Increase CPU/Memory

## uv Issues

### "uv command not found"

1. **Not inside devcontainer**: Command Palette → "Reopen in Container"
2. **Running locally**: Install uv: `curl -LsSf https://astral.sh/uv/install.sh | sh`
3. **PATH issue**: Add `export PATH="$HOME/.cargo/bin:$PATH"` to shell config

### "Lock file is outdated"

```bash
uv lock                    # Regenerate lock file
uv sync --group dev        # Install updated dependencies
git add pyproject.toml uv.lock
git commit -m "Update lock file"
```

### Package Not Found (ModuleNotFoundError)

1. **Dependencies not installed**: `uv sync --group dev`
2. **Package not added**: `uv add <package>`
3. **Wrong environment**: Use `uv run python` (not bare `python`)
4. **Dev dependency**: Use `uv sync --group dev` (not just `uv sync`)

### "No solution found" (Dependency Conflict)

```bash
# Try updating conflicting packages
uv lock --upgrade-package package-a
uv lock --upgrade-package package-c

# Or pin to compatible versions
uv add "package-a>=1.1.0"
```

## Python Interpreter Issues

### VSCode Can't Find Python Interpreter

1. Command Palette → "Python: Select Interpreter" → Choose `.venv/bin/python`
2. Run `uv sync --group dev` to create venv
3. Command Palette → "Developer: Reload Window"

### Wrong Python Version

1. **Not using container**: Reopen in Container
2. **Wrong image**: Check `.devcontainer/devcontainer.json` has `python:3.13`, rebuild
3. **System Python**: Use `uv run python --version`

## Dependency Issues

### Tests Pass Locally But Fail in CI

**Cause**: Usually uncommitted `uv.lock`

```bash
git status              # Check for uncommitted files
git add uv.lock
git commit -m "Update lock file"
git push
```

### Import Works in REPL But Not in Tests

1. **Add pythonpath** to `pyproject.toml`:
   ```toml
   [tool.pytest.ini_options]
   pythonpath = "src"
   ```

2. **Check imports** - use package name, not `src/`:
   ```python
   # ✅ Correct
   from example_project.main import hello

   # ❌ Wrong
   from src.example_project.main import hello
   ```

### Transitive Dependency Conflicts

```bash
# Update packages to find compatible versions
uv lock --upgrade-package package-a
uv lock --upgrade-package package-c
```

## Git Issues

### Merge Conflict in uv.lock

```bash
git checkout --ours uv.lock   # Accept either version
uv lock                       # Regenerate
git add uv.lock
git commit -m "Merge and regenerate lock file"
```

### Large Diff in uv.lock

This is **normal** when updating dependencies. The lock file captures the entire dependency tree. Review the diff, ensure no suspicious packages, then commit.

## Clean Slate

If all else fails:

```bash
rm -rf .venv/              # Remove virtual environment
rm -rf ~/.cache/uv         # Clear uv cache
# Command Palette → "Dev Containers: Rebuild Container Without Cache"
uv lock                    # Regenerate lock file
uv sync --group dev        # Reinstall everything
```

## Debugging

```bash
uv -vv sync --group dev    # Verbose uv output
python --version           # Check Python version
uv --version               # Check uv version
uv pip list                # List installed packages
```

## Resources

- **uv docs**: https://docs.astral.sh/uv/
- **devcontainer docs**: https://containers.dev/
- **ruff docs**: https://docs.astral.sh/ruff/
