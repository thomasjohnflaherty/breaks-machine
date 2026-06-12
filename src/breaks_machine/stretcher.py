"""Time-stretching audio using rubberband."""

import re
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path


class RubberbandNotFoundError(Exception):
    """Raised when rubberband CLI is not installed."""

    pass


class UnsupportedEngineError(Exception):
    """Raised when the requested rubberband engine is unavailable."""

    pass


def check_rubberband_installed() -> None:
    """
    Verify that rubberband CLI is installed and accessible.

    Raises:
        RubberbandNotFoundError: If rubberband is not found with install instructions.
    """
    if shutil.which("rubberband") is None:
        platform = sys.platform
        if platform == "darwin":
            install_cmd = "brew install rubberband"
        elif platform.startswith("linux"):
            install_cmd = "sudo apt-get install rubberband-cli"
        elif platform == "win32":
            install_cmd = "Download from https://breakfastquay.com/rubberband/"
        else:
            install_cmd = "See https://breakfastquay.com/rubberband/"

        raise RubberbandNotFoundError(
            f"rubberband CLI not found. Install it with:\n  {install_cmd}"
        )


@lru_cache(maxsize=1)
def get_rubberband_major_version() -> int | None:
    """
    Detect the installed rubberband major version.

    Returns:
        Major version number, or None if it cannot be determined.
    """
    try:
        result = subprocess.run(
            ["rubberband", "-V"],
            capture_output=True,
            text=True,
        )
    except OSError:
        return None

    output = (result.stdout or result.stderr).strip()
    match = re.search(r"(\d+)\.\d+", output)
    if match:
        return int(match.group(1))
    return None


def resolve_engine(engine: str = "auto") -> str:
    """
    Resolve the requested engine to "r2" or "r3".

    Args:
        engine: "auto", "r2", or "r3"

    Returns:
        "r3" if requested or auto-selected (rubberband >= 3), otherwise "r2".

    Raises:
        UnsupportedEngineError: If "r3" is forced but rubberband < 3.
    """
    version = get_rubberband_major_version()

    if engine == "r2":
        return "r2"

    if engine == "r3":
        if version is None or version < 3:
            found = version if version is not None else "unknown"
            raise UnsupportedEngineError(
                f"R3 engine requires rubberband >= 3 (found: {found}). "
                "Upgrade rubberband or use --engine r2."
            )
        return "r3"

    if version is not None and version >= 3:
        return "r3"
    return "r2"


def calculate_stretch_ratio(source_bpm: float, target_bpm: float) -> float:
    """
    Calculate the time stretch ratio to convert from source to target BPM.

    Args:
        source_bpm: Original tempo in BPM
        target_bpm: Desired tempo in BPM

    Returns:
        Stretch ratio as playback rate (>1 = faster, <1 = slower)
        This matches pyrubberband semantics for API compatibility.
    """
    # Return as playback rate: higher BPM = faster playback rate
    # To go from 170 BPM to 85 BPM (slower), we need rate = 85/170 = 0.5
    # To go from 85 BPM to 170 BPM (faster), we need rate = 170/85 = 2.0
    return target_bpm / source_bpm


def build_stretch_command(
    input_path: Path,
    output_path: Path,
    ratio: float,
    crispness: int = 5,
    engine: str = "auto",
) -> list[str]:
    """
    Build the rubberband command line for the resolved engine.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        ratio: Playback rate (>1 = faster, <1 = slower)
        crispness: Rubberband crispness setting (R2 engine only)
        engine: "auto", "r2", or "r3"

    Returns:
        Command argument list for subprocess.
    """
    resolved = resolve_engine(engine)

    if resolved == "r3":
        return [
            "rubberband",
            "--fine",
            "--centre-focus",
            "--tempo",
            str(ratio),
            "--quiet",
            str(input_path),
            str(output_path),
        ]

    return [
        "rubberband",
        "--tempo",
        str(ratio),
        "--crisp",
        str(crispness),
        "--quiet",
        str(input_path),
        str(output_path),
    ]


def stretch_audio(
    input_path: Path,
    output_path: Path,
    ratio: float,
    crispness: int = 5,
    engine: str = "auto",
) -> None:
    """
    Time-stretch audio file using rubberband CLI directly.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        ratio: Playback rate (>1 = faster, <1 = slower)
        crispness: Rubberband crispness setting (0-6, default 5 for drums)
                   Applies to the R2 engine only; ignored under R3.
        engine: Engine selection ("auto", "r2", or "r3"). Auto uses R3
                when rubberband >= 3, otherwise R2.
    """
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # No stretching needed - just copy the file
    if ratio == 1.0:
        shutil.copy2(input_path, output_path)
        return

    # Call rubberband CLI directly using --tempo (playback rate)
    # --tempo 2.0 = double speed (half duration)
    # --tempo 0.5 = half speed (double duration)
    command = build_stretch_command(input_path, output_path, ratio, crispness, engine)
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        raise RuntimeError(f"rubberband failed: {result.stderr}")


def stretch_to_bpm(
    input_path: Path,
    output_path: Path,
    source_bpm: float,
    target_bpm: float,
    crispness: int = 5,
    engine: str = "auto",
) -> None:
    """
    Convenience function to stretch audio from source BPM to target BPM.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        source_bpm: Original tempo in BPM
        target_bpm: Desired tempo in BPM
        crispness: Rubberband crispness setting (R2 engine only)
        engine: Engine selection ("auto", "r2", or "r3")
    """
    ratio = calculate_stretch_ratio(source_bpm, target_bpm)
    stretch_audio(input_path, output_path, ratio, crispness, engine)
