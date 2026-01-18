"""Audio format conversion utilities."""

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

    # Load audio
    y, sr = sf.read(input_path)
    input_info = sf.info(input_path)

    # Track if any conversion is needed
    needs_conversion = False

    # Resample if needed
    if sample_rate is not None and sample_rate != sr:
        needs_conversion = True
        # Use soxr for high-quality resampling (installed with librosa)
        import soxr

        y = soxr.resample(y, sr, sample_rate)
        sr = sample_rate

    # Convert to mono if needed
    if mono and len(y.shape) > 1 and y.shape[1] > 1:
        needs_conversion = True
        y = np.mean(y, axis=1)

    # Determine output subtype
    if bit_depth is not None:
        needs_conversion = True
        subtype = BIT_DEPTH_TO_SUBTYPE.get(bit_depth)
        if subtype is None:
            raise ValueError(f"Unsupported bit depth: {bit_depth}. Use 16, 24, or 32.")
    else:
        subtype = input_info.subtype

    # Only write if conversion was needed or output path differs
    if needs_conversion or output_path != input_path:
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
