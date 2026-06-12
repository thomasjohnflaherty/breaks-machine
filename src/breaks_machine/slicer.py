"""Slice-and-shift retiming (the ReCycle/jungle method)."""

import math
import shutil
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf

MIN_ONSETS = 4
CROSSFADE_S = 0.005
FADE_OUT_S = 0.010
SILENCE_THRESHOLD = 1e-4


def detect_slice_points(
    y: np.ndarray,
    sr: int,
    source_bpm: float,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Find slice cut points and their grid-quantized placement anchors.

    Onsets are detected on a mono mix with backtracking so cuts land in the
    quiet zone just before each transient. Each cut is snapped to its nearest
    16th-note grid line of the known source BPM; the snapped position drives
    target placement math while the audio is cut at the detected point.
    Falls back to pure 8th-note grid slicing when too few onsets are found.

    Args:
        y: Audio samples, mono (n,) or multichannel (n, channels)
        sr: Sample rate in Hz
        source_bpm: Known source tempo in BPM

    Returns:
        (cuts, anchors): sample indices to cut the audio at, and the grid
        positions used for each slice's target placement. Both start at 0.
    """
    n_samples = y.shape[0]
    mono = y if y.ndim == 1 else y.mean(axis=1)

    onsets = librosa.onset.onset_detect(y=mono, sr=sr, units="samples", backtrack=True)
    onsets = [int(o) for o in onsets if 0 < o < n_samples]

    if len(onsets) < MIN_ONSETS:
        step = sr * 60 / source_bpm / 2
        count = max(1, math.ceil(n_samples / step))
        cuts = np.array([round(i * step) for i in range(count)], dtype=np.int64)
        return cuts, cuts.copy()

    grid_step = sr * 60 / source_bpm / 4
    cuts = np.array(sorted({0, *onsets}), dtype=np.int64)
    anchors = np.array(
        [round(round(cut / grid_step) * grid_step) for cut in cuts],
        dtype=np.int64,
    )
    anchors[0] = 0
    return cuts, anchors


def _apply_gain(segment: np.ndarray, curve: np.ndarray) -> np.ndarray:
    if segment.ndim == 2:
        return segment * curve[:, np.newaxis]
    return segment * curve


def _fade_in(segment: np.ndarray, n: int) -> None:
    curve = np.sin(np.linspace(0.0, np.pi / 2, n))
    segment[:n] = _apply_gain(segment[:n], curve)


def _fade_out(segment: np.ndarray, n: int) -> None:
    curve = np.cos(np.linspace(0.0, np.pi / 2, n))
    segment[-n:] = _apply_gain(segment[-n:], curve)


def _tail_is_audible(segment: np.ndarray, index: int) -> bool:
    window = segment[max(0, index - 32) : index]
    return window.size > 0 and np.max(np.abs(window)) > SILENCE_THRESHOLD


def reslice_audio(
    y: np.ndarray,
    sr: int,
    source_bpm: float,
    target_bpm: float,
) -> np.ndarray:
    """
    Retime audio by moving slices on the timeline without stretching them.

    Each slice keeps its original samples bit-exact; only its start position
    scales by source_bpm / target_bpm. Slowing down opens gaps that each
    slice's natural decay rings into; speeding up overlaps slices with an
    equal-power crossfade where the later slice wins. Every splice point is
    faded or crossfaded so no discontinuities are introduced.

    Args:
        y: Audio samples, mono (n,) or multichannel (n, channels)
        sr: Sample rate in Hz
        source_bpm: Original tempo in BPM
        target_bpm: Desired tempo in BPM

    Returns:
        Retimed audio of length ceil(n * source_bpm / target_bpm).
    """
    factor = source_bpm / target_bpm
    n_samples = y.shape[0]
    cuts, anchors = detect_slice_points(y, sr, source_bpm)

    starts = np.round(anchors * factor).astype(np.int64) + (cuts - anchors)
    starts = np.maximum.accumulate(np.maximum(starts, 0))

    length = math.ceil(n_samples * factor)
    out_shape = (length,) if y.ndim == 1 else (length, y.shape[1])
    out = np.zeros(out_shape, dtype=np.float64)

    xfade = max(2, round(CROSSFADE_S * sr))
    fade_out = max(2, round(FADE_OUT_S * sr))
    bounds = np.append(cuts[1:], n_samples)

    fade_in_pending = False
    for i in range(len(cuts)):
        segment = np.array(y[cuts[i] : bounds[i]], dtype=np.float64)
        start = int(starts[i])
        if start >= length:
            break

        if fade_in_pending:
            _fade_in(segment, min(xfade, segment.shape[0]))
        fade_in_pending = False

        is_last = i == len(cuts) - 1
        next_start = length if is_last else int(starts[i + 1])
        end = start + segment.shape[0]

        if not is_last and end > next_start and _tail_is_audible(segment, next_start - start):
            segment = segment[: min(next_start + xfade, length) - start]
            _fade_out(segment, min(xfade, segment.shape[0]))
            fade_in_pending = True
        else:
            if end > length:
                segment = segment[: length - start]
            if _tail_is_audible(segment, segment.shape[0]):
                _fade_out(segment, min(fade_out, segment.shape[0]))

        out[start : start + segment.shape[0]] += segment

    return out


def slice_to_bpm(
    input_path: Path,
    output_path: Path,
    source_bpm: float,
    target_bpm: float,
) -> None:
    """
    Retime audio from source BPM to target BPM by slicing and shifting.

    Slices at detected onsets and moves them on the timeline; for slow-downs
    every transient is reproduced bit-exact since nothing is stretched.

    Args:
        input_path: Path to input audio file
        output_path: Path for output audio file
        source_bpm: Original tempo in BPM
        target_bpm: Desired tempo in BPM
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if target_bpm == source_bpm:
        shutil.copy2(input_path, output_path)
        return

    y, sr = sf.read(input_path)
    subtype = sf.info(input_path).subtype
    out = reslice_audio(y, sr, source_bpm, target_bpm)
    sf.write(output_path, out, sr, subtype=subtype)
