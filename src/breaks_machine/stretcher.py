"""Time-stretching audio using rubberband."""

import shutil
import subprocess
import sys
from pathlib import Path


class RubberbandNotFoundError(Exception):
    """Raised when rubberband CLI is not installed."""

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


def stretch_audio(
    input_path: Path,
    output_path: Path,
    ratio: float,
    crispness: int = 5,
) -> None:
    """
    Time-stretch audio file using rubberband CLI directly.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        ratio: Playback rate (>1 = faster, <1 = slower)
        crispness: Rubberband crispness setting (0-6, default 5 for drums)
                   Higher values preserve transients better.
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
    result = subprocess.run(
        [
            "rubberband",
            "--tempo",
            str(ratio),
            "--crisp",
            str(crispness),
            "--quiet",
            str(input_path),
            str(output_path),
        ],
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
) -> None:
    """
    Convenience function to stretch audio from source BPM to target BPM.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        source_bpm: Original tempo in BPM
        target_bpm: Desired tempo in BPM
        crispness: Rubberband crispness setting (0-6, default 5 for drums)
    """
    ratio = calculate_stretch_ratio(source_bpm, target_bpm)
    stretch_audio(input_path, output_path, ratio, crispness)
