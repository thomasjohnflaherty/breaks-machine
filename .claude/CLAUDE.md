# breaks-machine Development Guide

CLI tool for time-stretching drum breaks to target BPMs while preserving transient quality.

## Project Overview

**breaks-machine** is a command-line tool designed to time-stretch drum breaks to specific BPMs using Rubberband's industry-standard algorithm. It's perfect for preparing breaks for hardware samplers, live performance, or production workflows.

**Tech Stack:**
- **pyrubberband**: Python wrapper for Rubberband time-stretching
- **librosa**: Audio analysis and BPM detection
- **soundfile**: Audio I/O for WAV/FLAC files
- **click**: CLI framework
- **Python 3.13** with **uv** for package management

## Key Components

### Core Modules

- **[cli.py](../../src/breaks_machine/cli.py)** - Click-based CLI entry point
  - Handles command-line arguments and user input
  - Orchestrates the processing pipeline
  - Entry point: `breaks-machine stretch`

- **[detector.py](../../src/breaks_machine/detector.py)** - BPM detection
  - Parses BPM from filename patterns (e.g., `amen_170.wav`)
  - Multi-strategy librosa detection with subdivision correction
  - Priority: manual override → filename → auto-detection

- **[stretcher.py](../../src/breaks_machine/stretcher.py)** - Rubberband wrapper
  - Time-stretching with crispness=5 (optimized for drums)
  - Ratio calculation: `target_bpm / source_bpm`
  - Preserves transients and minimizes phase artifacts

- **[converter.py](../../src/breaks_machine/converter.py)** - Format conversion
  - Optional sample rate conversion
  - Bit depth conversion (16/24-bit)
  - Stereo to mono downmixing

- **[processor.py](../../src/breaks_machine/processor.py)** - Pipeline orchestration
  - Single file and batch directory processing
  - Output structure: `output/{filename}/{basename}_{bpm}.{ext}`
  - Target parsing (single, multiple, range modes)

## Development Workflow

### Testing

```bash
# Run all tests
uv run pytest tests

# Run with coverage
uv run pytest tests --cov=src/breaks_machine

# Run specific test file
uv run pytest tests/test_detector.py -v

# Watch mode (if using pytest-watch)
uv run ptw tests/
```

### Code Quality

```bash
# Format code
uvx ruff format

# Lint and fix issues
uvx ruff check --fix

# Check formatting without changes
uvx ruff format --check

# Full quality check
uvx ruff check && uvx ruff format --check
```

### Manual Testing

Test with real drum breaks in the `breaks/` directory:

```bash
# Test filename pattern detection (rename file first if needed)
uv run breaks-machine stretch breaks/FR_Drum_Loop_160.wav -t 140

# Test with manual BPM override (recommended for files without BPM in filename)
uv run breaks-machine stretch breaks/amen_RUDE.wav --bpm 175 -t 140

# Test batch processing (ensure files have BPM in filename)
uv run breaks-machine stretch breaks/ --targets 90,120,140 -o test_output/

# Note: Auto-detection is unreliable - always use filename patterns or --bpm flag
```

## Audio Processing Notes

### Supported Formats

- **Input**: WAV, FLAC
- **Output**: Same format as input (preserves original format by default)

### Rubberband Crispness Settings

The `--crispness` parameter (0-6) controls transient preservation:

- **0-2**: Smoother, less transient preservation (not ideal for drums)
- **3-4**: Balanced
- **5**: Default for breaks-machine - optimized for drums
- **6**: Maximum transient preservation

### BPM Detection Improvements

Recent improvements to `detector.py`:

- **Filename pattern detection** (reliable):
  - Leading patterns: `164_HT_Drums.wav → 164 BPM`
  - With "bpm" suffix: `amen-170bpm.wav → 170 BPM`
  - Trailing patterns: `amen_170.wav → 170 BPM`
  - Range limited to 90-180 BPM (typical breakbeat range)

- **Auto-detection with librosa** (experimental, often unreliable):
  - Multi-strategy detection with multiple tempo priors (120, 140, 170 BPM)
  - Subdivision correction for common misdetections (half-time, 2/3 time, etc.)
  - Smart selection preferring direct detections over derived subdivisions
  - Breakbeat bias toward 140-180 BPM range
  - **Note**: Auto-detection frequently produces incorrect results. Filename patterns or `--bpm` manual override are strongly recommended.

**Development guideline**: When testing, always use files with BPM in the filename or the `--bpm` flag. Do not rely on auto-detection for accurate results.

### System Dependencies

Required for time-stretching functionality:

- **rubberband-cli**: The actual time-stretching engine
- **libsndfile1**: Audio file I/O library
- **ffmpeg**: Audio codec support

**Installation:**

**macOS:**
```bash
brew install rubberband
```

**Ubuntu/Debian:**
```bash
sudo apt-get install rubberband-cli libsndfile1 ffmpeg
```

**Windows:**
Download from https://breakfastquay.com/rubberband/ and add to PATH.

## Quick Reference

### Common Commands

- Add dependency: `uv add <package>`
- Add dev dependency: `uv add --dev <package>`
- Run CLI: `uv run breaks-machine stretch <file> [options]`
- Run tests: `uv run pytest tests`
- Format code: `uvx ruff format`
- Lint code: `uvx ruff check --fix`

### CLI Usage Examples

```bash
# Single target
breaks-machine stretch amen_170.wav --target 140

# Multiple targets
breaks-machine stretch break.wav --targets 90,120,140,160

# Range with step
breaks-machine stretch break.wav --range 80-160 --step 10

# Batch directory
breaks-machine stretch ./breaks/ -t 140 -o ./output/

# With format conversion
breaks-machine stretch break.wav -t 140 --sample-rate 44100 --mono

# Manual BPM override
breaks-machine stretch break.wav --bpm 175 -t 140
```

### Important Files

- `pyproject.toml` - Project metadata and dependency specifications
- `uv.lock` - Locked dependency tree (always commit!)
- `.python-version` - Python version pinning (3.13)
- `src/breaks_machine/` - Source code
- `tests/` - Test suite
- `breaks/` - Test audio files for manual testing
- `.github/workflows/ci.yml` - CI/CD pipeline configuration
- `.github/workflows/release.yml` - PyPI release automation

## Detailed Documentation

For more information about the development environment and tooling:

- **uv quick reference**: [.claude/rules/uv-guide.md](rules/uv-guide.md)
- **CI/CD pipeline**: [.claude/rules/cicd.md](rules/cicd.md)
- **Troubleshooting**: [.claude/rules/troubleshooting.md](rules/troubleshooting.md)

## Project Principles

- **Reproducibility**: `uv.lock` ensures identical dependencies across all environments
- **Standard Python package**: Installable via pip/uv
- **Quality first**: Comprehensive test suite with 58 tests, all passing
- **Fast feedback**: Linting and formatting enforced in CI/CD
- **Easy distribution**: Automated PyPI releases on version tags
