# Claude Code Setup in Devcontainer

This project supports **two devcontainer configurations** for different authentication methods.

## Prerequisites

1. **Docker Desktop** - Required for devcontainers
2. **VSCode** with the "Dev Containers" extension
3. **Authentication method** - Choose one:
   - **Claude Pro subscription** (personal use - session auth)
   - **API key** (work environments - from https://console.anthropic.com/settings/keys)

## Personal Setup (Session Authentication)

Use this if you have a **Claude Pro subscription** and want to use session authentication.

### Setup Steps

1. **Ensure personal devcontainer is active**:
   - The `.devcontainer` folder should be configured for personal use (default)
   - If you previously used work setup, run:
     ```bash
     mv .devcontainer .devcontainer-work
     mv .devcontainer-personal .devcontainer
     rm .claude/settings.json .claude/api_key_helper.sh 2>/dev/null || true
     ```

2. **Open in devcontainer**:
   - VSCode → Reopen in Container
   - Wait for container to build

3. **Authenticate inside container**:
   ```bash
   claude login
   ```
   - Follow OAuth flow in browser
   - Credentials persist in mounted `~/.claude` directory

### How It Works

- Mounts your **global** `~/.claude` directory from host into container
- Uses Claude Pro session authentication (OAuth)
- Credentials persist across container rebuilds
- No API key needed

### Troubleshooting

**"Invalid bearer token" error after login:**
- This means stale credentials exist in the project's `.claude` folder
- Fix:
  ```bash
  rm .claude/settings.json .claude/api_key_helper.sh 2>/dev/null || true
  # Rebuild container
  ```

**Login loop (keeps asking to authenticate):**
- Check if `~/.claude/.credentials.json` exists on host
- If not, authenticate on host first: `claude login`
- Then rebuild container

## Work Setup (API Key Authentication)

Use this if you have an **Anthropic API key** and want automatic authentication.

### Setup Steps

1. **Switch to work devcontainer**:
   ```bash
   mv .devcontainer .devcontainer-personal
   mv .devcontainer-work .devcontainer
   ```

2. **Set API key on host machine**:

   **macOS/Linux (zsh):**
   ```bash
   echo 'export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-KEY-HERE"' >> ~/.zshrc
   source ~/.zshrc
   ```

   **macOS/Linux (bash):**
   ```bash
   echo 'export ANTHROPIC_API_KEY="sk-ant-api03-YOUR-KEY-HERE"' >> ~/.bashrc
   source ~/.bashrc
   ```

   **Windows (PowerShell - run as Administrator):**
   ```powershell
   [System.Environment]::SetEnvironmentVariable('ANTHROPIC_API_KEY', 'sk-ant-api03-YOUR-KEY-HERE', 'User')
   ```

3. **Restart VSCode completely** (Cmd+Q on Mac, Alt+F4 on Windows)

4. **Open in devcontainer**:
   - VSCode inherits env vars from shell
   - Reopen in Container
   - API key automatically configured

### How It Works

- Passes API key from host → container via `remoteEnv`
- Creates API key helper script in `.claude/settings.json`
- Mounts **project's** `.claude` folder for persistence
- Works around OAuth limitations in devcontainers

### Troubleshooting

**Claude Code asks me to login:**

1. **Check API key on host:**
   ```bash
   # OUTSIDE container
   echo $ANTHROPIC_API_KEY
   ```
   If empty, set it following steps above.

2. **Check API key in container:**
   ```bash
   # INSIDE container
   echo $ANTHROPIC_API_KEY
   ```
   If empty, quit VSCode and reopen from terminal.

3. **Check helper script:**
   ```bash
   # INSIDE container
   cat ~/.claude/api_key_helper.sh
   cat ~/.claude/settings.json
   ```
   If missing, rebuild container.

**"Invalid API key" error:**
- Verify key at https://console.anthropic.com/settings/keys
- Check full key was copied (they're long)
- Verify API credits in Anthropic account

## Switching Between Configs

### Work → Personal

```bash
mv .devcontainer .devcontainer-work
mv .devcontainer-personal .devcontainer
rm .claude/settings.json .claude/api_key_helper.sh 2>/dev/null || true
# Rebuild container, then run: claude login
```

### Personal → Work

```bash
mv .devcontainer .devcontainer-personal
mv .devcontainer-work .devcontainer
# Ensure ANTHROPIC_API_KEY is set on host
# Rebuild container
```

## General Troubleshooting

### Container fails to build

Check logs: VSCode Output panel → "Dev Containers"

Common causes:
- Docker Desktop not running
- Insufficient disk space
- Network issues

### Permission errors with ~/.claude

The devcontainer automatically fixes permissions on startup via `postAttachCommand`.

### Need fresh start

```bash
rm -rf .claude/  # Clear project Claude config
# Rebuild container without cache
```

## Security Notes

### Personal Setup
- Session credentials stored in `~/.claude/.credentials.json` on host
- Mounted into container (not copied)
- Never commit `.claude/` directory

### Work Setup
- API key stored only in shell config
- Passed via environment variable
- Never commit API key to version control
- Each developer uses their own key

## Cost

- **Personal (session auth)**: Included with Claude Pro subscription
- **Work (API key)**: Uses API credits from Anthropic Console
  - Monitor usage: https://console.anthropic.com/settings/cost

## Additional Resources

- [Claude Code Documentation](https://code.claude.com/docs)
- [Anthropic Console](https://console.anthropic.com)
- [GitHub Issue #1736](https://github.com/anthropics/claude-code/issues/1736) - Session auth in devcontainers
- [GitHub Issue #14528](https://github.com/anthropics/claude-code/issues/14528) - API key auth in devcontainers
