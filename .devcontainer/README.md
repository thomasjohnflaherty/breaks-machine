# Personal Devcontainer (Session Authentication)

This is the **personal setup** using Claude Pro session authentication.

## When to Use This

Use this configuration if you have a **Claude Pro subscription** and want to use session authentication (OAuth).

## Features

- Mounts your global `~/.claude` directory from host
- Uses Claude Pro session authentication
- No API key needed
- Credentials persist across container rebuilds

## Setup

1. Ensure this is the active `.devcontainer` folder
2. Open in devcontainer
3. Run `claude login` inside the container
4. Follow OAuth flow in browser

## Authentication

After container starts, authenticate with:
```bash
claude login
```

Your credentials will be stored in your host's `~/.claude/.credentials.json` and persist across rebuilds.

## System Dependencies

Automatically installs:
- `rubberband-cli` - Time-stretching engine
- `libsndfile1` - Audio I/O library
- `ffmpeg` - Audio codec support
- `@anthropic-ai/claude-code` - Claude Code CLI

See [.claude/rules/claude-code-setup.md](../.claude/rules/claude-code-setup.md) for more details.
