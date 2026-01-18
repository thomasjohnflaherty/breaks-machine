# Work Devcontainer (API Key Authentication)

This is the **work setup** using Anthropic API key authentication.

## When to Use This

Use this configuration if you have an **Anthropic API key** (from https://console.anthropic.com/settings/keys).

## Features

- Uses API key from host environment variable
- Automatically configured on container start
- No manual login required
- Good for work environments where you have API credits

## Setup

1. **Set API key on host machine**:

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

2. **Restart VS Code completely** (Cmd+Q on Mac, Alt+F4 on Windows)

3. **Switch to this devcontainer**:
   ```bash
   mv .devcontainer .devcontainer-personal
   mv .devcontainer-work .devcontainer
   ```

4. **Reopen in Container**

The API key will be automatically configured via the helper script.

## Authentication

Authentication happens automatically using the `ANTHROPIC_API_KEY` environment variable. No manual login required.

## System Dependencies

Automatically installs:
- `rubberband-cli` - Time-stretching engine
- `libsndfile1` - Audio I/O library
- `ffmpeg` - Audio codec support
- `@anthropic-ai/claude-code` - Claude Code CLI

## Cost

Uses API credits from your Anthropic Console account. Monitor usage at: https://console.anthropic.com/settings/cost

See [.claude/rules/claude-code-setup.md](../.claude/rules/claude-code-setup.md) for more details.
