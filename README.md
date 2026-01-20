# breaks-machine

[![PyPI version](https://badge.fury.io/py/breaks-machine.svg)](https://pypi.org/project/breaks-machine/)
[![CI](https://github.com/thomasjohnflaherty/breaks-machine/actions/workflows/ci.yml/badge.svg)](https://github.com/thomasjohnflaherty/breaks-machine/actions/workflows/ci.yml)
[![codecov](https://codecov.io/gh/thomasjohnflaherty/breaks-machine/branch/main/graph/badge.svg)](https://codecov.io/gh/thomasjohnflaherty/breaks-machine)
[![Python 3.13+](https://img.shields.io/badge/python-3.13+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Time-stretch drum breaks to target BPMs while preserving transient quality.

Perfect for preparing drum breaks for hardware samplers, live performance, or production workflows where you need breaks at specific tempos.

## Features

- **BPM Detection from Filenames**: Automatically parses BPM from common filename patterns (e.g., `amen_170.wav`, `164_break.flac`)
- **Multiple Target Modes**: Stretch to single BPM, multiple targets, or ranges with custom steps
- **Batch Processing**: Process entire directories of breaks in one command
- **High-Quality Stretching**: Uses Rubberband with crispness=5 optimized for transient preservation
- **Format Conversion**: Optional sample rate, bit depth, and channel conversion
- **Manual BPM Override**: Specify exact source BPM with `--bpm` flag when needed

## Requirements

### System Dependencies

**Rubberband** is required for time-stretching:

**macOS:**
```bash
brew install rubberband
```

**Ubuntu/Debian:**
```bash
sudo apt-get install rubberband-cli libsndfile1 ffmpeg
```

**Windows:**
Download Rubberband from [https://breakfastquay.com/rubberband/](https://breakfastquay.com/rubberband/) and add to PATH.

### Python

Python 3.13+ required.

## Installation

**With uv (recommended):**
```bash
uv tool install breaks-machine
```

**With pip:**
```bash
pip install breaks-machine
```

**From source:**
```bash
git clone https://github.com/thomasjohnflaherty/breaks-machine.git
cd breaks-machine
uv sync
```

## Quick Start

### Single File, Single Target

Stretch a break to 140 BPM:
```bash
breaks-machine stretch amen_170.wav --target 140
```

Output: `output/amen_170/amen_140.wav`

### Multiple Targets

Create versions at different BPMs:
```bash
breaks-machine stretch amen_170.wav --targets 90,120,140,160
```

Output:
```
output/amen_170/
├── amen_90.wav
├── amen_120.wav
├── amen_140.wav
└── amen_160.wav
```

### BPM Range

Generate versions across a range:
```bash
breaks-machine stretch break.wav --range 80-160 --step 10
```

Creates versions at 80, 90, 100, ..., 160 BPM.

### Batch Processing

Process an entire directory:
```bash
breaks-machine stretch ./breaks/ --target 140 --output ./processed/
```

### With Manual BPM Override

If auto-detection fails or you know the correct tempo:
```bash
breaks-machine stretch break.wav --bpm 175 --target 140
```

## CLI Reference

```
breaks-machine stretch INPUT_PATH [OPTIONS]
```

### Arguments

- `INPUT_PATH`: Path to audio file (.wav, .flac) or directory containing audio files

### Options

**Target Specification** (required, choose one):
- `-t, --target BPM`: Single target BPM
- `--targets BPM,BPM,...`: Comma-separated target BPMs
- `-r, --range START-END`: BPM range with optional step

**BPM Detection**:
- `-b, --bpm BPM`: Manual source BPM override
- `-w, --warn`: Warn if detected BPM differs from filename

**Output**:
- `-o, --output DIR`: Output directory (default: `./output`)

**Format Conversion**:
- `--sample-rate HZ`: Target sample rate (e.g., 44100, 48000)
- `--bit-depth {16,24}`: Target bit depth
- `--mono`: Convert to mono

**Stretching**:
- `--crispness {0-6}`: Rubberband crispness (default: 5, higher preserves transients)
- `-s, --step N`: Step size for range mode (default: 10)

### Examples

**Basic usage**:
```bash
# Stretch to single target
breaks-machine stretch amen_170.wav -t 140

# Multiple targets
breaks-machine stretch break.wav --targets 90,120,140

# Range with custom step
breaks-machine stretch break.wav --range 100-140 --step 5
```

**With format conversion**:
```bash
# Convert to 44.1kHz mono 16-bit
breaks-machine stretch break.wav -t 140 --sample-rate 44100 --bit-depth 16 --mono
```

**Batch processing**:
```bash
# Process directory
breaks-machine stretch ./breaks/ -t 140 -o ./output/

# With manual BPM for all files
breaks-machine stretch ./breaks/ -t 140 --bpm 170
```

## How It Works

### Architecture

```
Input Audio → BPM Detection → Time Stretching → Format Conversion → Output
                    ↓                 ↓                  ↓
              detector.py       stretcher.py      converter.py
```

### BPM Detection Priority

1. **Manual Override** (`--bpm`): If specified, uses this value (most reliable)
2. **Filename Parsing**: Automatically detects BPM from these patterns:
   - **With "bpm" suffix**: `amen-170bpm.wav`, `break_140_BPM.flac`, `drum-loop-120bpm.wav`
   - **Leading number**: `164_HT_Drums.wav`, `140_break.flac`, `120-drums.wav`
   - **Trailing number**: `amen_170.wav`, `break-140.flac`, `drums_90.wav`
   - **Range**: Must be 90-180 BPM to avoid false matches
3. **Auto-Detection** (experimental): Falls back to librosa-based detection if no filename pattern found
   - **Warning**: Auto-detection is experimental and often produces incorrect results
   - **Recommended**: Use filename patterns or `--bpm` flag for reliable results
   - Multi-strategy detection with tempo priors and subdivision correction
   - May misidentify tempo by factors of 2x, 0.5x, or other subdivisions

**Best Practice**: Name your files with BPM in the filename (e.g., `amen_170.wav`) or use the `--bpm` flag to ensure accurate time-stretching.

### Rubberband Crispness

The tool uses crispness=5 by default, which:
- Preserves transients (drum hits)
- Minimizes phase artifacts
- Optimized for percussive material

You can adjust with `--crispness {0-6}` (higher = more transient preservation).

## Supported Formats

- **Input**: WAV, FLAC
- **Output**: Same format as input (or specify conversion options)

## Troubleshooting

### BPM Detection Issues

If breaks-machine cannot detect the BPM or produces incorrect results:

**Problem**: "Could not determine BPM" error

**Solutions**:
1. **Add BPM to filename** (recommended):
   ```bash
   # Rename your file to include BPM
   mv break.wav break_140.wav
   breaks-machine stretch break_140.wav -t 120
   ```

2. **Use manual BPM override**:
   ```bash
   breaks-machine stretch break.wav --bpm 140 -t 120
   ```

**Problem**: Auto-detection finds wrong BPM (e.g., detects 85 BPM instead of 170 BPM)

**Why**: Librosa's tempo detection can be unreliable on drum breaks, often misidentifying tempo by factors of 2x or 0.5x. This appears to be related to the version of the Rubberband CLI tool available (pre-4.0.0).

**Solution**: Always use filename patterns or `--bpm` flag:
```bash
# Good filename patterns
amen_170.wav        # Trailing number
164_break.flac      # Leading number
drums-140bpm.wav    # With "bpm" suffix

# Or use manual override
breaks-machine stretch break.wav --bpm 170 -t 140
```

**Problem**: Batch processing with mixed BPMs

**Solution**: Ensure all files follow naming conventions or use individual processing with `--bpm` per file.

## Development

### Local Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/breaks-machine.git
   cd breaks-machine
   ```

2. **Install system dependencies** (see Requirements above)

3. **Install Python dependencies**:
   ```bash
   uv sync --group dev
   ```

4. **Run tests**:
   ```bash
   uv run pytest tests
   ```

### Running Tests

```bash
# All tests
uv run pytest tests

# With coverage
uv run pytest tests --cov=src/breaks_machine

# Specific test file
uv run pytest tests/test_detector.py -v
```

### Code Quality

```bash
# Format code
uvx ruff format

# Lint code
uvx ruff check --fix

# Type checking (if added)
uvx mypy src/
```

### Manual Testing

The repository includes test breaks in the `breaks/` directory:
```bash
# Test with real breaks
uv run breaks-machine stretch breaks/FR_Drum_Loop_160.wav -t 140
```

### Project Structure

```
src/breaks_machine/
├── cli.py          # Click-based CLI entry point
├── detector.py     # BPM detection (filename + librosa)
├── stretcher.py    # Rubberband wrapper
├── converter.py    # Format conversion
└── processor.py    # Processing pipeline

tests/
├── test_cli.py
├── test_detector.py
├── test_stretcher.py
├── test_converter.py
└── test_processor.py
```

## Technical Details

### Dependencies

- **click**: CLI framework
- **librosa**: Audio analysis and BPM detection
- **pyrubberband**: Python wrapper for Rubberband
- **soundfile**: Audio I/O for WAV/FLAC

### System Requirements

- **rubberband-cli**: Time-stretching engine
- **libsndfile1**: Audio file I/O library
- **ffmpeg**: Audio codec support

See the Requirements section for platform-specific installation instructions.

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `uv run pytest tests`
5. Format code: `uvx ruff format`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

**Note:** breaks-machine requires Rubberband CLI (GPL v2) as a system dependency. While breaks-machine itself is MIT licensed, you must comply with Rubberband's GPL v2 license when using it.

## Acknowledgments

- **Rubberband**: Industry-standard time-stretching library
- **librosa**: Audio analysis toolkit
- Built with modern Python tooling (uv, ruff, pytest)
