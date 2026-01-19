"""Pipeline orchestration for processing drum breaks."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from .converter import convert_audio
from .detector import get_source_bpm
from .stretcher import stretch_to_bpm

# Supported audio extensions
SUPPORTED_EXTENSIONS = {".wav", ".flac"}


def _noop_echo(_: str) -> None:
    """No-op function for echo when none is provided."""
    pass


@dataclass
class ProcessingOptions:
    """Options for audio processing."""

    manual_bpm: float | None = None
    sample_rate: int | None = None
    bit_depth: int | None = None
    mono: bool = False
    warn: bool = False
    crispness: int = 5


def is_audio_file(path: Path) -> bool:
    """Check if a path is a supported audio file."""
    return path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS


def strip_bpm_from_filename(filename: str) -> str:
    """
    Remove BPM suffix from filename.

    Examples:
        amen_170 -> amen
        break-140bpm -> break
        loop_160_BPM -> loop
        funky_break -> funky_break (no change)
    """
    # Pattern 1: number followed by optional separator and "bpm" (case insensitive)
    # e.g., "140bpm", "140-bpm", "140_BPM", "140 bpm"
    pattern_with_bpm = r"[\s_-]?(\d{2,3})[\s_-]?bpm"
    result = re.sub(pattern_with_bpm, "", filename, flags=re.IGNORECASE)

    # Pattern 2: underscore/hyphen followed by 2-3 digit number at end
    # e.g., "_170", "-85" at the end
    pattern_trailing = r"[_-](\d{2,3})$"
    result = re.sub(pattern_trailing, "", result)

    return result


def generate_output_path(
    input_path: Path,
    output_dir: Path,
    target_bpm: float,
) -> Path:
    """
    Generate output path following the naming convention.

    Structure: output_dir/{original_filename}/{basename}_{target_bpm}.{ext}

    Examples:
        amen_170.wav @ 140 -> output/amen_170/amen_140.wav
        funky_break.wav @ 120 -> output/funky_break/funky_break_120.wav
    """
    stem = input_path.stem
    ext = input_path.suffix
    folder = output_dir / stem

    # Strip BPM from filename before adding target BPM
    base_name = strip_bpm_from_filename(stem)
    filename = f"{base_name}_{int(target_bpm)}{ext}"

    return folder / filename


def process_file(
    input_path: Path,
    targets: list[float],
    output_dir: Path,
    options: ProcessingOptions,
    echo: Callable[[str], None] | None = None,
) -> list[Path]:
    """
    Process a single audio file to multiple target BPMs.

    Args:
        input_path: Path to input audio file
        targets: List of target BPMs
        output_dir: Base output directory
        options: Processing options
        echo: Optional callback for status messages

    Returns:
        List of created output file paths
    """
    if echo is None:
        echo = _noop_echo

    # Detect source BPM
    echo(f"Detecting BPM for {input_path.name}...")
    source_bpm = get_source_bpm(
        input_path,
        manual_bpm=options.manual_bpm,
        warn=options.warn,
        warn_callback=echo,
    )
    echo(f"  Source BPM: {source_bpm}")

    output_paths = []

    for target_bpm in targets:
        output_path = generate_output_path(input_path, output_dir, target_bpm)
        echo(f"  Stretching to {int(target_bpm)} BPM -> {output_path}")

        # Time stretch
        stretch_to_bpm(
            input_path,
            output_path,
            source_bpm,
            target_bpm,
            crispness=options.crispness,
        )

        # Apply format conversion if any options specified
        if options.sample_rate or options.bit_depth or options.mono:
            convert_audio(
                output_path,
                output_path,
                sample_rate=options.sample_rate,
                bit_depth=options.bit_depth,
                mono=options.mono,
            )

        output_paths.append(output_path)

    return output_paths


def process_directory(
    input_dir: Path,
    targets: list[float],
    output_dir: Path,
    options: ProcessingOptions,
    echo: Callable[[str], None] | None = None,
) -> list[Path]:
    """
    Process all audio files in a directory.

    Args:
        input_dir: Directory containing audio files
        targets: List of target BPMs
        output_dir: Base output directory
        options: Processing options
        echo: Optional callback for status messages

    Returns:
        List of all created output file paths
    """
    if echo is None:
        echo = _noop_echo

    # Find all audio files
    audio_files = sorted([f for f in input_dir.iterdir() if is_audio_file(f)])

    if not audio_files:
        raise ValueError(f"No audio files found in {input_dir}")

    echo(f"Found {len(audio_files)} audio file(s)")

    all_outputs = []

    for audio_file in audio_files:
        outputs = process_file(audio_file, targets, output_dir, options, echo)
        all_outputs.extend(outputs)

    return all_outputs


def parse_targets(
    target: float | None,
    targets: str | None,
    range_spec: str | None,
    step: int,
) -> list[float]:
    """
    Parse target BPM specifications into a list of BPMs.

    Args:
        target: Single target BPM
        targets: Comma-separated target BPMs
        range_spec: Range specification (e.g., "80-160")
        step: Step size for range

    Returns:
        List of target BPMs

    Raises:
        ValueError: If no valid targets specified
    """
    result = []

    if target is not None:
        result.append(target)

    if targets is not None:
        for t in targets.split(","):
            result.append(float(t.strip()))

    if range_spec is not None:
        parts = range_spec.split("-")
        if len(parts) != 2:
            raise ValueError(f"Invalid range format: {range_spec}. Use 'start-end'.")
        start = int(parts[0])
        end = int(parts[1])
        result.extend(float(bpm) for bpm in range(start, end + 1, step))

    if not result:
        raise ValueError("No target BPM specified. Use --target, --targets, or --range.")

    # Remove duplicates while preserving order
    seen = set()
    unique = []
    for bpm in result:
        if bpm not in seen:
            seen.add(bpm)
            unique.append(bpm)

    return unique
