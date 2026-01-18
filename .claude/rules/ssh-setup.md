# SSH Keys in Devcontainer

## Current Configuration

SSH keys from the host machine are mounted into the devcontainer to enable git operations with SSH authentication (GitHub, Bitbucket, GitLab, etc.).

### Configuration in devcontainer.json

```json
"mounts": [
    "source=${localEnv:HOME}${localEnv:USERPROFILE}/.ssh,target=/home/vscode/.ssh,type=bind,consistency=cached"
],

"postCreateCommand": "mkdir -p ~/.ssh && chmod 700 ~/.ssh && find ~/.ssh -maxdepth 1 -type f -exec chmod 600 {} + && uv sync --group dev"
```

## How It Works

- **Host SSH directory**: Your local `~/.ssh` directory is mounted into the container (writable)
- **Container location**: Accessible at `/home/vscode/.ssh` inside the container
- **Auto-permission fixing**: `postCreateCommand` automatically sets correct permissions on container startup
- **Cross-platform**: Works on Windows (USERPROFILE), macOS/Linux (HOME)
- **known_hosts support**: Container can add new host keys to `~/.ssh/known_hosts` as needed

## Verification After Container Rebuild

```bash
# Check SSH directory is mounted
ls -la ~/.ssh/

# Test SSH agent (if using one)
ssh-add -l

# Test GitHub connection
ssh -T git@github.com

# Test Bitbucket connection
ssh -T git@bitbucket.org
```

## Troubleshooting

### Permission Errors
Permission errors should be automatically fixed by the `postCreateCommand`. If you still encounter issues:
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/id_*
chmod 644 ~/.ssh/*.pub
```

### Host Key Verification Failed
If you get "Host key verification failed" for a new git host:
```bash
# Add the host to known_hosts
ssh-keyscan github.com >> ~/.ssh/known_hosts
ssh-keyscan bitbucket.org >> ~/.ssh/known_hosts

# Or accept on first connection
ssh -T git@github.com  # Type 'yes' when prompted
```

### Using Specific Keys
Configure git to use a specific key:
```bash
git config --global core.sshCommand "ssh -i ~/.ssh/your_specific_key"
```

## History

- **Issue**: SSH keys not accessible in devcontainer for git operations
- **Previous attempt**: Added SSH agent configuration that broke the container
- **First solution**: Mount-based approach with readonly flag
- **Issue**: readonly flag prevented adding new hosts to known_hosts
- **Final solution**: Writable mount + automatic permission fixing via postCreateCommand
- **Status**: ✅ Configuration complete, requires container rebuild to apply
