"""Time-stretching audio using rubberband."""

import shutil
import sys
from pathlib import Path

import pyrubberband
import soundfile as sf


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
        Stretch ratio for pyrubberband (>1 means faster/shorter, <1 means slower/longer)
    """
    # pyrubberband rate: >1 = faster (shorter duration), <1 = slower (longer duration)
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
    Time-stretch audio file using rubberband.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        ratio: Time stretch ratio (>1 = slower, <1 = faster)
        crispness: Rubberband crispness setting (0-6, default 5 for drums)
                   Higher values preserve transients better.
    """
    # Load audio
    y, sr = sf.read(input_path)

    # pyrubberband expects mono or stereo as (samples,) or (samples, channels)
    # soundfile returns (samples, channels) for stereo, (samples,) for mono

    # Map crispness to pyrubberband options
    # Crispness 5 = "--crispness 5" which is good for drums
    # pyrubberband uses rbargs as a dict
    rbargs = {"--crispness": str(crispness)}

    # Time stretch
    y_stretched = pyrubberband.time_stretch(y, sr, ratio, rbargs=rbargs)

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Determine subtype based on input file format
    input_info = sf.info(input_path)
    subtype = input_info.subtype

    # Write output with same format as input
    sf.write(output_path, y_stretched, sr, subtype=subtype)


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
