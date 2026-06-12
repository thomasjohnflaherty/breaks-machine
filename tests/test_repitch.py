"""Tests for repitch and hybrid processing."""

import math

import numpy as np
import pytest
import soundfile as sf

from breaks_machine.repitch import (
    hybrid_to_bpm,
    repitch_audio,
    repitch_to_bpm,
    split_tempo_factor,
)


@pytest.fixture
def sine_file(tmp_path):
    """1-second 440 Hz sine at 44100 Hz."""
    sr = 44100
    t = np.linspace(0, 1.0, sr, endpoint=False)
    audio = 0.8 * np.sin(2 * np.pi * 440 * t)
    path = tmp_path / "sine_440.wav"
    sf.write(path, audio, sr, subtype="PCM_16")
    return path


def dominant_frequency(path):
    y, sr = sf.read(path)
    spectrum = np.abs(np.fft.rfft(y))
    freqs = np.fft.rfftfreq(len(y), 1 / sr)
    return freqs[np.argmax(spectrum)]


class TestSplitTempoFactor:
    """Tests for the repitch/stretch factor split."""

    def test_within_max_stretch_passthrough(self):
        """Moderate slowdown should be pure stretch (170 -> 140)."""
        factor = 140 / 170
        semitones, residual = split_tempo_factor(factor, 3.0)
        assert semitones == 0.0
        assert residual == factor

    def test_speedup_within_max_stretch_passthrough(self):
        """Moderate speedup should be pure stretch."""
        semitones, residual = split_tempo_factor(1.3, 3.0)
        assert semitones == 0.0
        assert residual == 1.3

    def test_capped_at_max_semitones(self):
        """Extreme slowdown caps the repitch at max_semitones (170 -> 90)."""
        factor = 90 / 170
        semitones, residual = split_tempo_factor(factor, 3.0)
        assert semitones == -3.0
        assert residual == pytest.approx(factor / 2 ** (-3 / 12))
        assert residual == pytest.approx(0.6296, abs=1e-4)
        assert 2 ** (semitones / 12) * residual == pytest.approx(factor)

    def test_exact_fit(self):
        """When the ideal repitch is under the cap, residual hits 1/1.4 exactly."""
        factor = 2 ** (-2 / 12) / 1.4
        semitones, residual = split_tempo_factor(factor, 3.0)
        assert semitones == pytest.approx(-2.0)
        assert residual == pytest.approx(1 / 1.4)

    def test_speedup_capped(self):
        """Extreme speedup repitches upward."""
        semitones, residual = split_tempo_factor(2.0, 3.0)
        assert semitones == 3.0
        assert residual == pytest.approx(2.0 / 2 ** (3 / 12))

    def test_decomposition_identity(self):
        """Semitones and residual always recompose to the original factor."""
        for factor in (0.5, 0.7, 0.9, 1.0, 1.2, 1.6, 2.0):
            semitones, residual = split_tempo_factor(factor, 3.0)
            assert 2 ** (semitones / 12) * residual == pytest.approx(factor)


class TestRepitchAudio:
    """Tests for vinyl-style repitching."""

    def test_slowdown_duration(self, sine_file, tmp_path):
        """Rate 0.5 should double the duration (within 1%)."""
        output = tmp_path / "out.wav"
        repitch_audio(sine_file, output, 0.5)
        assert sf.info(output).duration == pytest.approx(2.0, rel=0.01)

    def test_slowdown_drops_pitch(self, sine_file, tmp_path):
        """Rate 0.5 should drop 440 Hz to ~220 Hz."""
        output = tmp_path / "out.wav"
        repitch_audio(sine_file, output, 0.5)
        assert dominant_frequency(output) == pytest.approx(220, abs=2)

    def test_speedup_duration_and_pitch(self, sine_file, tmp_path):
        """Rate 2.0 should halve duration and raise 440 Hz to ~880 Hz."""
        output = tmp_path / "out.wav"
        repitch_audio(sine_file, output, 2.0)
        assert sf.info(output).duration == pytest.approx(0.5, rel=0.01)
        assert dominant_frequency(output) == pytest.approx(880, abs=4)

    def test_preserves_sample_rate_and_subtype(self, sine_file, tmp_path):
        output = tmp_path / "out.wav"
        repitch_audio(sine_file, output, 0.75)
        info = sf.info(output)
        assert info.samplerate == 44100
        assert info.subtype == "PCM_16"

    def test_unity_rate_copies(self, sine_file, tmp_path):
        output = tmp_path / "out.wav"
        repitch_audio(sine_file, output, 1.0)
        assert sf.info(output).duration == pytest.approx(1.0, rel=0.001)


class TestRepitchToBpm:
    """Tests for BPM-driven repitching."""

    def test_duration_matches_bpm_ratio(self, sine_file, tmp_path):
        """170 -> 90 should lengthen by 170/90 (within 1%)."""
        output = tmp_path / "out.wav"
        repitch_to_bpm(sine_file, output, 170, 90)
        assert sf.info(output).duration == pytest.approx(170 / 90, rel=0.01)

    def test_semitone_shift_170_to_90(self, sine_file, tmp_path):
        """Slowing 170 -> 90 should drop pitch by ~11 semitones."""
        output = tmp_path / "out.wav"
        repitch_to_bpm(sine_file, output, 170, 90)
        shift = 12 * math.log2(dominant_frequency(output) / 440)
        assert shift == pytest.approx(12 * math.log2(90 / 170), abs=0.1)


class TestHybridToBpm:
    """Tests for hybrid repitch+stretch."""

    def test_moderate_change_skips_repitch(self, sine_file, tmp_path, monkeypatch):
        """Within 1.4x the input goes straight to the stretcher."""
        calls = []

        def fake_stretch(input_path, output_path, ratio, crispness, engine):
            calls.append((input_path, output_path, ratio, crispness, engine))

        monkeypatch.setattr("breaks_machine.repitch.stretch_audio", fake_stretch)

        output = tmp_path / "out.wav"
        hybrid_to_bpm(sine_file, output, 170, 140, max_semitones=3.0)

        assert len(calls) == 1
        assert calls[0][0] == sine_file
        assert calls[0][2] == pytest.approx(140 / 170)

    def test_extreme_change_repitches_then_stretches(self, sine_file, tmp_path, monkeypatch):
        """170 -> 90 repitches by -3 st, then stretches the residual."""
        calls = []

        def fake_stretch(input_path, output_path, ratio, crispness, engine):
            calls.append((input_path, output_path, ratio))
            assert sf.info(input_path).duration == pytest.approx(2 ** (3 / 12), rel=0.01)

        monkeypatch.setattr("breaks_machine.repitch.stretch_audio", fake_stretch)

        output = tmp_path / "out.wav"
        hybrid_to_bpm(sine_file, output, 170, 90, max_semitones=3.0)

        assert len(calls) == 1
        intermediate, _, ratio = calls[0]
        assert intermediate != sine_file
        assert ratio == pytest.approx((90 / 170) / 2 ** (-3 / 12))
        assert not intermediate.exists()

    def test_end_to_end_duration(self, sine_file, tmp_path):
        """Real rubberband run: total duration matches 170 -> 90."""
        output = tmp_path / "out.wav"
        hybrid_to_bpm(sine_file, output, 170, 90, max_semitones=3.0)
        assert sf.info(output).duration == pytest.approx(170 / 90, rel=0.05)
