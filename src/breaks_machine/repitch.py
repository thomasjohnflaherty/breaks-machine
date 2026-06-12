"""Vinyl-style repitching and hybrid repitch+stretch processing."""

import math
import shutil
import tempfile
from pathlib import Path

import soundfile as sf
import soxr

from .stretcher import stretch_audio

MAX_STRETCH = 1.4


def split_tempo_factor(
    tempo_factor: float,
    max_semitones: float,
    max_stretch: float = MAX_STRETCH,
) -> tuple[float, float]:
    """
    Split a tempo factor into a repitch amount and a residual stretch factor.

    Args:
        tempo_factor: Playback rate (target_bpm / source_bpm)
        max_semitones: Cap on the repitch magnitude in semitones
        max_stretch: Maximum duration change the stretch stage should absorb

    Returns:
        (semitones, residual_factor) such that
        tempo_factor == 2 ** (semitones / 12) * residual_factor.
        semitones is 0.0 when the stretch alone stays within max_stretch,
        negative when slowing down, positive when speeding up, with
        magnitude capped at max_semitones.
    """
    if 1 / max_stretch <= tempo_factor <= max_stretch:
        return 0.0, tempo_factor

    if tempo_factor < 1:
        semitones = 12 * math.log2(tempo_factor * max_stretch)
        semitones = max(semitones, -max_semitones)
    else:
        semitones = 12 * math.log2(tempo_factor / max_stretch)
        semitones = min(semitones, max_semitones)

    residual = tempo_factor / 2 ** (semitones / 12)
    return semitones, residual


def repitch_audio(input_path: Path, output_path: Path, rate: float) -> None:
    """
    Repitch audio by resampling, changing speed and pitch together.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        rate: Playback rate (>1 = faster and higher pitch,
              <1 = slower and lower pitch)
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if rate == 1.0:
        shutil.copy2(input_path, output_path)
        return

    y, sr = sf.read(input_path)
    subtype = sf.info(input_path).subtype
    y = soxr.resample(y, sr * rate, sr)
    sf.write(output_path, y, sr, subtype=subtype)


def repitch_to_bpm(
    input_path: Path,
    output_path: Path,
    source_bpm: float,
    target_bpm: float,
) -> None:
    """
    Repitch audio from source BPM to target BPM (vinyl-style speed change).

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        source_bpm: Original tempo in BPM
        target_bpm: Desired tempo in BPM
    """
    repitch_audio(input_path, output_path, target_bpm / source_bpm)


def hybrid_to_bpm(
    input_path: Path,
    output_path: Path,
    source_bpm: float,
    target_bpm: float,
    max_semitones: float = 3.0,
    crispness: int = 5,
    engine: str = "auto",
) -> None:
    """
    Split the tempo change between a repitch and a time-stretch.

    Repitches by up to max_semitones to keep the residual stretch within
    MAX_STRETCH, then time-stretches the remainder with rubberband.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        source_bpm: Original tempo in BPM
        target_bpm: Desired tempo in BPM
        max_semitones: Cap on the repitch magnitude in semitones
        crispness: Rubberband crispness setting (R2 engine only)
        engine: Engine selection ("auto", "r2", or "r3")
    """
    tempo_factor = target_bpm / source_bpm
    semitones, residual = split_tempo_factor(tempo_factor, max_semitones)

    if semitones == 0.0:
        stretch_audio(input_path, output_path, residual, crispness, engine)
        return

    with tempfile.NamedTemporaryFile(suffix=input_path.suffix, delete=False) as tmp:
        tmp_path = Path(tmp.name)
    try:
        repitch_audio(input_path, tmp_path, 2 ** (semitones / 12))
        stretch_audio(tmp_path, output_path, residual, crispness, engine)
    finally:
        tmp_path.unlink(missing_ok=True)
