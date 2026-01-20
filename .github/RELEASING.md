# Release Process

This document explains how to release new versions of breaks-machine to PyPI.

## Prerequisites

### 1. Create PyPI Account

1. Go to [PyPI](https://pypi.org) and create an account
2. Verify your email address
3. Enable two-factor authentication (2FA) - **required** for uploading packages

### 2. Create API Token

1. Go to your [PyPI account settings](https://pypi.org/manage/account/)
2. Scroll to "API tokens" section
3. Click "Add API token"
   - Token name: `breaks-machine-github-actions`
   - Scope: "Entire account" (first time) or "Project: breaks-machine" (after first release)
4. Copy the token (starts with `pypi-`)
5. **Save it immediately** - you won't be able to see it again

### 3. Add Token to GitHub Secrets

1. Go to your GitHub repo → Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Name: `PYPI_API_TOKEN`
4. Value: Paste your PyPI API token
5. Click "Add secret"

## Release Workflow

Once the token is configured, releases are automated:

### 1. Update Version

Edit `pyproject.toml` and bump the version:

```toml
[project]
name = "breaks-machine"
version = "0.2.0"  # <- Update this
```

### 2. Update CHANGELOG.md

Add release notes for the new version following Keep a Changelog format.

### 3. Commit Changes

```bash
git add pyproject.toml CHANGELOG.md
git commit -m "Bump version to 0.2.0"
git push
```

### 4. Create and Push Tag

```bash
git tag v0.2.0
git push origin v0.2.0
```

### 5. Automated Steps

The GitHub Actions workflow will automatically:
1. ✅ Build the package
2. ✅ Publish to PyPI
3. ✅ Create GitHub Release with package files

### 6. Verify Release

- Check [PyPI](https://pypi.org/project/breaks-machine/)
- Check [GitHub Releases](https://github.com/thomasjohnflaherty/breaks-machine/releases)
- Test installation: `pip install breaks-machine`

## Version Numbering

Use [Semantic Versioning](https://semver.org/):

- **Major** (1.0.0): Breaking changes
- **Minor** (0.1.0): New features, backwards compatible
- **Patch** (0.0.1): Bug fixes, backwards compatible

## Pre-Release Checklist

Before releasing any version:

- [ ] **CHANGELOG.md updated** with release notes for this version
- [ ] **README.md is complete and accurate** for this release
- [ ] **Documentation reviewed** for accuracy (features, examples, known issues)
- [ ] All tests passing in CI
- [ ] Version number updated in `pyproject.toml`
- [ ] Committed all changes
- [ ] Ready to tag and push

## First Release Checklist

Before releasing v0.1.0:

- [ ] PyPI account created and verified
- [ ] API token created and added to GitHub secrets
- [ ] README.md is complete and accurate
- [ ] CHANGELOG.md created with v0.1.0 notes
- [ ] All tests passing in CI
- [ ] Version set to `0.1.0` in pyproject.toml
- [ ] Tag pushed: `git tag v0.1.0 && git push origin v0.1.0`

## Troubleshooting

### "Package name already exists"

If `breaks-machine` is already taken on PyPI:
1. Choose a new name (e.g., `breaks-machine-cli`)
2. Update `name` in `pyproject.toml`
3. Update `project.scripts` entry point

### "Invalid token"

- Verify token is copied correctly (starts with `pypi-`)
- Check token hasn't expired
- Ensure 2FA is enabled on PyPI account

### "Build failed"

- Run `uv build` locally to test
- Check `pyproject.toml` syntax
- Ensure all files are committed

## Testing Before Release

Test the package build locally:

```bash
# Build package
uv build

# Install locally
pip install dist/breaks_machine-0.1.0-py3-none-any.whl

# Test CLI
breaks-machine --version
```

## Post-Release

After a successful release:

1. Update README if needed
2. Consider adding changelog/release notes
3. Announce on social media, forums, etc.
4. Monitor PyPI download stats
