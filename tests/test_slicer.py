"""Tests for slice-and-shift retiming."""

import math

import numpy as np
import pytest
import soundfile as sf

from breaks_machine.slicer import detect_slice_points, reslice_audio, slice_to_bpm

SR = 44100


def make_click_track(bpm=120, clicks=8, sr=SR, stereo=False):
    """Decaying 1 kHz bursts at exact quarter-note spacing."""
    spacing = round(sr * 60 / bpm)
    audio = np.zeros(spacing * clicks)
    t = np.arange(round(0.05 * sr)) / sr
    burst = np.sin(2 * np.pi * 1000 * t) * np.exp(-t * 240)
    attack = round(0.002 * sr)
    burst[:attack] *= np.linspace(0, 1, attack)
    burst *= 0.8 / np.max(np.abs(burst))
    for i in range(clicks):
        audio[i * spacing : i * spacing + len(burst)] += burst
    if stereo:
        audio = np.column_stack([audio, audio * 0.5])
    return audio


def find_clicks(y, sr, thresh=0.3, min_gap=0.2):
    """Threshold-based onset finder, deterministic for click tracks."""
    mono = y if y.ndim == 1 else y[:, 0]
    loud = np.where(np.abs(mono) > thresh)[0]
    onsets = []
    last = -sr
    for i in loud:
        if i - last > min_gap * sr:
            onsets.append(int(i))
        last = int(i)
    return onsets


class TestResliceClickTrack:
    """Tests for slice-and-shift on a synthetic click track."""

    def test_slowdown_duration(self):
        """120 -> 60 should double the duration (within 1%)."""
        y = make_click_track()
        out = reslice_audio(y, SR, 120, 60)
        assert out.shape[0] == pytest.approx(2 * y.shape[0], rel=0.01)

    def test_slowdown_click_positions(self):
        """Clicks land within a few ms of their re-spaced positions."""
        y = make_click_track()
        out = reslice_audio(y, SR, 120, 60)

        in_clicks = find_clicks(y, SR)
        out_clicks = find_clicks(out, SR)
        assert len(out_clicks) == len(in_clicks) == 8

        spacing = round(SR * 60 / 120)
        lag = in_clicks[0]
        for i, onset in enumerate(out_clicks):
            assert abs(onset - (2 * i * spacing + lag)) < 0.003 * SR

    def test_no_clicks_at_splice_points(self):
        """Re-spacing must not introduce discontinuities beyond the input's."""
        y = make_click_track()
        out = reslice_audio(y, SR, 120, 60)
        assert np.max(np.abs(np.diff(out))) <= np.max(np.abs(np.diff(y))) * 1.1

    def test_speedup_duration(self):
        """120 -> 150 shortens by 120/150 with overlapping slices crossfaded."""
        y = make_click_track()
        out = reslice_audio(y, SR, 120, 150)
        assert out.shape[0] == math.ceil(y.shape[0] * 120 / 150)
        assert np.all(np.isfinite(out))


class TestGridFallback:
    """Tests for pure grid slicing when onsets are undetectable."""

    @pytest.fixture
    def onset_free(self):
        return np.zeros(2 * SR)

    def test_falls_back_to_eighth_note_grid(self, onset_free):
        cuts, anchors = detect_slice_points(onset_free, SR, 120)
        step = SR * 60 / 120 / 2
        assert len(cuts) == math.ceil(len(onset_free) / step)
        assert np.array_equal(cuts, anchors)
        assert cuts[0] == 0

    def test_fallback_output_duration(self, onset_free):
        out = reslice_audio(onset_free, SR, 120, 60)
        assert out.shape[0] == 2 * len(onset_free)


class TestSliceToBpm:
    """Tests for the file-level API."""

    def test_stereo_preserved(self, tmp_path):
        """2ch in -> 2ch out, sample rate and subtype preserved."""
        y = make_click_track(stereo=True)
        input_path = tmp_path / "stereo_120.wav"
        sf.write(input_path, y, SR, subtype="PCM_24")

        output = tmp_path / "out.wav"
        slice_to_bpm(input_path, output, 120, 60)

        info = sf.info(output)
        assert info.channels == 2
        assert info.samplerate == SR
        assert info.subtype == "PCM_24"
        assert info.duration == pytest.approx(2 * y.shape[0] / SR, rel=0.01)

    def test_same_bpm_copies(self, tmp_path):
        y = make_click_track()
        input_path = tmp_path / "clicks_120.wav"
        sf.write(input_path, y, SR, subtype="PCM_16")

        output = tmp_path / "out.wav"
        slice_to_bpm(input_path, output, 120, 120)

        assert output.read_bytes() == input_path.read_bytes()
