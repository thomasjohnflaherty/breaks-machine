"""Audio format conversion utilities."""

import shutil
from pathlib import Path

import numpy as np
import soundfile as sf

# Map bit depth to soundfile subtype
BIT_DEPTH_TO_SUBTYPE = {
    16: "PCM_16",
    24: "PCM_24",
    32: "PCM_32",
}


def convert_audio(
    input_path: Path,
    output_path: Path | None = None,
    sample_rate: int | None = None,
    bit_depth: int | None = None,
    mono: bool = False,
) -> Path:
    """
    Convert audio file format, sample rate, bit depth, and/or channels.

    Args:
        input_path: Path to input audio file
        output_path: Path for output file (defaults to overwriting input)
        sample_rate: Target sample rate in Hz (e.g., 44100, 48000)
        bit_depth: Target bit depth (16 or 24)
        mono: Convert to mono if True

    Returns:
        Path to the output file
    """
    if output_path is None:
        output_path = input_path

    input_info = sf.info(input_path)

    if bit_depth is not None:
        subtype = BIT_DEPTH_TO_SUBTYPE.get(bit_depth)
        if subtype is None:
            raise ValueError(f"Unsupported bit depth: {bit_depth}. Use 16, 24, or 32.")
    else:
        subtype = input_info.subtype

    needs_resample = sample_rate is not None and sample_rate != input_info.samplerate
    needs_mono = mono and input_info.channels > 1
    needs_subtype = subtype != input_info.subtype

    if not (needs_resample or needs_mono or needs_subtype):
        if output_path != input_path:
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(input_path, output_path)
        return output_path

    y, sr = sf.read(input_path)

    if needs_resample:
        # Use soxr for high-quality resampling (installed with librosa)
        import soxr

        y = soxr.resample(y, sr, sample_rate)
        sr = sample_rate

    if needs_mono and y.ndim > 1:
        y = np.mean(y, axis=1)

    # libsndfile wraps out-of-range floats on integer write; normalize only on overflow
    peak = np.max(np.abs(y))
    if peak > 1.0:
        y = y / peak

    if subtype == "PCM_16":
        rng = np.random.default_rng()
        lsb = 1.0 / 32768.0
        y = y + (rng.random(y.shape) + rng.random(y.shape) - 1.0) * lsb
        y = np.clip(y, -1.0, 1.0)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sf.write(output_path, y, sr, subtype=subtype)

    return output_path


def get_audio_info(file_path: Path) -> dict:
    """
    Get audio file information.

    Args:
        file_path: Path to audio file

    Returns:
        Dictionary with audio properties
    """
    info = sf.info(file_path)
    return {
        "sample_rate": info.samplerate,
        "channels": info.channels,
        "frames": info.frames,
        "duration": info.duration,
        "format": info.format,
        "subtype": info.subtype,
    }
