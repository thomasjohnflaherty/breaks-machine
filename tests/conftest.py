"""Test fixtures and configuration."""

from pathlib import Path

import numpy as np
import pytest
import soundfile as sf


@pytest.fixture
def fixtures_dir() -> Path:
    """Return the path to the fixtures directory."""
    return Path(__file__).parent / "fixtures"


@pytest.fixture
def temp_audio_file(tmp_path: Path) -> Path:
    """
    Create a temporary test audio file.

    Returns a 1-second mono audio file at 44100 Hz.
    """
    # Create a simple drum-like sound (click with decay)
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # Create 4 "hits" at 120 BPM (2 hits per second = 120 BPM)
    audio = np.zeros_like(t)
    hit_times = [0.0, 0.5]  # Two hits in 1 second = 120 BPM

    for hit_time in hit_times:
        hit_idx = int(hit_time * sr)
        # Exponential decay "click"
        decay_samples = int(0.1 * sr)  # 100ms decay
        decay = np.exp(-np.linspace(0, 5, decay_samples))
        # Add some noise burst
        noise = np.random.randn(decay_samples) * decay
        end_idx = min(hit_idx + decay_samples, len(audio))
        audio[hit_idx:end_idx] = noise[: end_idx - hit_idx]

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.8

    # Save to temp file
    output_path = tmp_path / "test_break_120.wav"
    sf.write(output_path, audio, sr, subtype="PCM_16")

    return output_path


@pytest.fixture
def temp_audio_file_170bpm(tmp_path: Path) -> Path:
    """
    Create a temporary test audio file at 170 BPM.

    The filename includes the BPM for testing filename parsing.
    """
    sr = 44100
    duration = 1.0
    t = np.linspace(0, duration, int(sr * duration), endpoint=False)

    # 170 BPM = 2.83 beats per second
    # For a 1 second file, we'll have roughly 2.83 beats
    beat_interval = 60.0 / 170.0  # ~0.353 seconds between beats
    audio = np.zeros_like(t)

    beat_time = 0.0
    while beat_time < duration:
        hit_idx = int(beat_time * sr)
        if hit_idx >= len(audio):
            break
        decay_samples = int(0.05 * sr)
        decay = np.exp(-np.linspace(0, 8, decay_samples))
        noise = np.random.randn(decay_samples) * decay
        end_idx = min(hit_idx + decay_samples, len(audio))
        audio[hit_idx:end_idx] = noise[: end_idx - hit_idx]
        beat_time += beat_interval

    audio = audio / np.max(np.abs(audio)) * 0.8

    output_path = tmp_path / "amen_170.wav"
    sf.write(output_path, audio, sr, subtype="PCM_16")

    return output_path


@pytest.fixture
def temp_stereo_file(tmp_path: Path) -> Path:
    """Create a stereo audio file for testing mono conversion."""
    sr = 44100
    duration = 0.5
    samples = int(sr * duration)

    # Create stereo audio (2 channels)
    left = np.random.randn(samples) * 0.5
    right = np.random.randn(samples) * 0.5
    audio = np.column_stack([left, right])

    output_path = tmp_path / "stereo_test.wav"
    sf.write(output_path, audio, sr, subtype="PCM_16")

    return output_path
