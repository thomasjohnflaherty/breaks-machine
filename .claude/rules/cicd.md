# CI/CD Pipeline Guide

## Pipeline Overview

**File**: `.github/workflows/ci.yml`

### Pipeline Stages

```
Trigger (push to any branch, pull request to main)
  ↓
Job: Lint, Format Check, and Test
  ↓
1. Checkout code (actions/checkout@v4)
  ↓
2. Setup Python (actions/setup-python@v5)
  ↓
3. Install uv (astral-sh/setup-uv@v7 with caching)
  ↓
4. Lint (uvx ruff check)
  ↓
5. Format check (uvx ruff format --check)
  ↓
6. Test (uv run pytest tests)
```

### Key Characteristics

- **Runner**: `ubuntu-latest` (Ubuntu 22.04 with Python pre-installed)
- **Python setup**: Via `actions/setup-python@v5` reading `.python-version`
- **uv setup**: Via official `astral-sh/setup-uv@v7` action
- **Consistency**: Uses same uv commands as local development
- **Lock file**: Uses `uv.lock` for reproducible dependencies
- **Caching**: Built-in uv cache via `enable-cache: true`

## Current Configuration

```yaml
name: CI

on:
  push:
    branches: ["*"]
  pull_request:
    branches: ["main"]

jobs:
  lint-format-test:
    name: Lint, Format Check, and Test
    runs-on: ubuntu-latest

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"

      - name: Install uv
        uses: astral-sh/setup-uv@v7
        with:
          version: "0.9.22"
          enable-cache: true

      - name: Verify uv installation
        run: uv --version

      - name: Lint with Ruff
        run: uvx ruff check

      - name: Check code formatting with Ruff
        run: uvx ruff format --check

      - name: Run tests with pytest
        run: uv run pytest tests
```

## How It Works

### Step 1: Checkout Code
```yaml
- name: Checkout code
  uses: actions/checkout@v4
```
Clones the repository code into the runner workspace.

### Step 2: Set up Python
```yaml
- name: Set up Python
  uses: actions/setup-python@v5
  with:
    python-version-file: ".python-version"
```
Installs Python 3.13 by reading the `.python-version` file. Uses GitHub's pre-cached Python versions for fast setup.

### Step 3: Install uv
```yaml
- name: Install uv
  uses: astral-sh/setup-uv@v7
  with:
    version: "0.9.22"
    enable-cache: true
```
Installs uv package manager with version pinning and automatic caching enabled.

### Step 4: Lint
```bash
uvx ruff check
```
Runs ruff linter. Fails workflow if linting errors found.

### Step 5: Format Check
```bash
uvx ruff format --check
```
Verifies code is properly formatted without modifying files.

### Step 6: Test
```bash
uv run pytest tests
```
Installs dependencies from `uv.lock` automatically and runs pytest.

## Trigger Conditions

**Push to any branch**:
```yaml
on:
  push:
    branches: ["*"]
```

**Pull requests to main**:
```yaml
on:
  pull_request:
    branches: ["main"]
```

**Both triggers combined**:
```yaml
on:
  push:
    branches: ["*"]
  pull_request:
    branches: ["main"]
```

### Common Modifications

**Run on specific branch patterns**:
```yaml
on:
  push:
    branches:
      - main
      - 'feature/**'
      - 'release/*'
```

**Run only on tagged commits**:
```yaml
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    name: Release build
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t myapp:${{ github.ref_name }} .
```

**Scheduled builds**:
```yaml
on:
  schedule:
    - cron: '0 0 * * *'  # Daily at midnight UTC
  push:
    branches: ["main"]

jobs:
  nightly-tests:
    name: Nightly tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
      - run: uv run pytest tests
```

**Matrix builds** (test multiple Python versions):
```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12", "3.13"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
      - run: uv run pytest tests
```

## Secrets and Environment Variables

### Setting Secrets

1. GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add name and value (e.g., `API_KEY`, `DATABASE_URL`, `DOCKER_PASSWORD`)

### Using Secrets

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version-file: ".python-version"
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
      - name: Run tests with secrets
        env:
          API_KEY: ${{ secrets.API_KEY }}
          DATABASE_URL: ${{ secrets.DATABASE_URL }}
        run: uv run pytest tests
```

### Environment Variables

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    env:
      DEBUG: "true"
      ENVIRONMENT: "ci"
    steps:
      - uses: actions/checkout@v4
      - run: uv run pytest tests  # DEBUG and ENVIRONMENT available
```

### Reusable Workflows

Create `.github/workflows/reusable-test.yml`:
```yaml
name: Reusable Test Workflow

on:
  workflow_call:
    inputs:
      python-version:
        required: false
        type: string
        default: "3.13"

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ inputs.python-version }}
      - uses: astral-sh/setup-uv@v7
        with:
          enable-cache: true
      - run: uv run pytest tests
```

Use it in another workflow:
```yaml
jobs:
  call-test:
    uses: ./.github/workflows/reusable-test.yml
    with:
      python-version: "3.13"
```

## Common CI Issues

### Tests Pass Locally But Fail in CI

**Cause**: Uncommitted `uv.lock` or local-only changes.

**Solution**:
```bash
git status  # Check for uncommitted files
git add uv.lock
git commit -m "Update lock file"
git push
```

### Workflow Not Triggering

**Causes**:
1. Workflow file has syntax errors (check Actions tab for parsing errors)
2. GitHub Actions not enabled for the repository
3. Branch protection rules blocking workflow runs

**Solution**:
1. Validate YAML syntax
2. Settings → Actions → General → Enable "Allow all actions and reusable workflows"
3. Settings → Branches → Check branch protection settings

### Caching Not Working

Check workflow logs for cache hit/miss messages:
```
Run astral-sh/setup-uv@v7
  Cache hit: ~/.cache/uv
```

If cache misses frequently, verify:
1. `enable-cache: true` is set in setup-uv step
2. `uv.lock` file is committed
3. Cache hasn't been manually cleared

### Debugging

Run the same commands locally:
```bash
uvx ruff check
uvx ruff format --check
uv run pytest tests
```

Use GitHub Actions locally with [act](https://github.com/nektos/act):
```bash
# Install act
brew install act  # macOS
# or: https://github.com/nektos/act#installation

# Run workflow locally
act push
```

## Best Practices

1. **Keep CI commands identical to local**: Use same commands in CI as local development
2. **Always commit `uv.lock`**: Ensures CI uses same dependency versions
3. **Fail fast**: Put linting before tests (faster feedback)
4. **Use caching**: Enable built-in caching with `enable-cache: true`
5. **Pin action versions**: Use `@v4` not `@latest` for reproducibility
6. **Protect main branch**: Require status checks to pass before merging (Settings → Branches → Branch protection rules)
7. **Use concurrency control**: Prevent multiple runs on same PR
   ```yaml
   concurrency:
     group: ${{ github.workflow }}-${{ github.ref }}
     cancel-in-progress: true
   ```

## Viewing Workflow Results

1. **Actions tab**: Click "Actions" in repository navigation
2. **Workflow runs**: See all runs with status (success, failure, in progress)
3. **Logs**: Click a run → Click job name → Expand steps to see detailed logs
4. **Re-run failed jobs**: Click "Re-run jobs" button on failed runs

## Branch Protection

Require CI to pass before merging:

1. Settings → Branches → Add branch protection rule
2. Branch name pattern: `main`
3. Enable "Require status checks to pass before merging"
4. Search for and select: "Lint, Format Check, and Test"
5. Enable "Require branches to be up to date before merging"
6. Save changes

## Cost & Limits

**Free tier** (public repos):
- 2,000 minutes/month for private repos
- Unlimited minutes for public repos

**This project's usage**:
- ~2-3 minutes per run (first run with cache miss)
- ~1-2 minutes per run (subsequent runs with cache hit)
- Well within free tier limits

## Resources

- **GitHub Actions docs**: https://docs.github.com/en/actions
- **Using uv in GitHub Actions**: https://docs.astral.sh/uv/guides/integration/github/
- **astral-sh/setup-uv**: https://github.com/astral-sh/setup-uv
- **Workflow syntax**: https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions
- **uv documentation**: https://docs.astral.sh/uv/
