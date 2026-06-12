"""Tests for audio stretching."""

import subprocess
from pathlib import Path

import pytest
import soundfile as sf

from breaks_machine.stretcher import (
    UnsupportedEngineError,
    build_stretch_command,
    calculate_stretch_ratio,
    check_rubberband_installed,
    get_rubberband_major_version,
    resolve_engine,
    stretch_audio,
    stretch_to_bpm,
)


@pytest.fixture(autouse=True)
def clear_version_cache():
    get_rubberband_major_version.cache_clear()
    yield
    get_rubberband_major_version.cache_clear()


def _mock_version_output(monkeypatch, stdout="", stderr="", raises=None):
    def fake_run(cmd, capture_output, text):
        if raises is not None:
            raise raises
        return subprocess.CompletedProcess(cmd, 0, stdout=stdout, stderr=stderr)

    monkeypatch.setattr("breaks_machine.stretcher.subprocess.run", fake_run)


class TestCalculateStretchRatio:
    """Tests for stretch ratio calculation."""

    def test_same_bpm(self):
        """Same BPM should give ratio of 1."""
        assert calculate_stretch_ratio(120, 120) == 1.0

    def test_slower_target(self):
        """Slower target BPM should give ratio < 1 (longer duration)."""
        # 170 to 85 = rate 0.5 (half speed = longer duration)
        assert calculate_stretch_ratio(170, 85) == 0.5

    def test_faster_target(self):
        """Faster target BPM should give ratio > 1 (shorter duration)."""
        # 85 to 170 = rate 2.0 (double speed = shorter duration)
        assert calculate_stretch_ratio(85, 170) == 2.0

    def test_arbitrary_ratio(self):
        """Test arbitrary BPM conversion."""
        # 120 to 140 = 140/120 = 1.167 (faster = shorter)
        ratio = calculate_stretch_ratio(120, 140)
        assert abs(ratio - (140 / 120)) < 0.001


class TestCheckRubberbandInstalled:
    """Tests for rubberband installation check."""

    def test_rubberband_available(self):
        """Test that rubberband check passes when installed."""
        # This should not raise since we installed rubberband
        check_rubberband_installed()


class TestGetRubberbandMajorVersion:
    """Tests for rubberband version detection."""

    def test_parses_modern_version(self, monkeypatch):
        """Version like '4.0.0' should parse to major 4."""
        _mock_version_output(monkeypatch, stdout="4.0.0\n")
        assert get_rubberband_major_version() == 4

    def test_parses_legacy_version(self, monkeypatch):
        """Version like '1.8.1' should parse to major 1."""
        _mock_version_output(monkeypatch, stdout="1.8.1\n")
        assert get_rubberband_major_version() == 1

    def test_parses_version_on_stderr(self, monkeypatch):
        """Some builds print the version to stderr."""
        _mock_version_output(monkeypatch, stderr="Rubber Band Library v3.3.0\n")
        assert get_rubberband_major_version() == 3

    def test_unparseable_output_returns_none(self, monkeypatch):
        """Garbage output should yield None."""
        _mock_version_output(monkeypatch, stdout="not a version")
        assert get_rubberband_major_version() is None

    def test_missing_binary_returns_none(self, monkeypatch):
        """OSError from subprocess should yield None."""
        _mock_version_output(monkeypatch, raises=FileNotFoundError("rubberband"))
        assert get_rubberband_major_version() is None

    def test_result_is_cached(self, monkeypatch):
        """Version detection should only invoke rubberband once."""
        calls = []

        def fake_run(cmd, capture_output, text):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="4.0.0\n", stderr="")

        monkeypatch.setattr("breaks_machine.stretcher.subprocess.run", fake_run)
        assert get_rubberband_major_version() == 4
        assert get_rubberband_major_version() == 4
        assert len(calls) == 1


class TestResolveEngine:
    """Tests for engine selection logic."""

    def test_auto_selects_r3_on_modern_rubberband(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 4)
        assert resolve_engine("auto") == "r3"

    def test_auto_falls_back_to_r2_on_legacy_rubberband(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 2)
        assert resolve_engine("auto") == "r2"

    def test_auto_falls_back_to_r2_when_version_unknown(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: None)
        assert resolve_engine("auto") == "r2"

    def test_forced_r2(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 4)
        assert resolve_engine("r2") == "r2"

    def test_forced_r3_on_modern_rubberband(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 3)
        assert resolve_engine("r3") == "r3"

    def test_forced_r3_on_legacy_rubberband_errors(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 2)
        with pytest.raises(UnsupportedEngineError, match="requires rubberband >= 3"):
            resolve_engine("r3")

    def test_forced_r3_with_unknown_version_errors(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: None)
        with pytest.raises(UnsupportedEngineError, match="unknown"):
            resolve_engine("r3")


class TestBuildStretchCommand:
    """Tests for rubberband command construction."""

    def test_r3_command(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 4)
        cmd = build_stretch_command(Path("in.wav"), Path("out.wav"), 0.8, crispness=5, engine="r3")
        assert cmd == [
            "rubberband",
            "--fine",
            "--centre-focus",
            "--tempo",
            "0.8",
            "--quiet",
            "in.wav",
            "out.wav",
        ]

    def test_r2_command(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 4)
        cmd = build_stretch_command(Path("in.wav"), Path("out.wav"), 0.8, crispness=6, engine="r2")
        assert cmd == [
            "rubberband",
            "--tempo",
            "0.8",
            "--crisp",
            "6",
            "--quiet",
            "in.wav",
            "out.wav",
        ]

    def test_auto_uses_r3_flags_on_modern_rubberband(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 4)
        cmd = build_stretch_command(Path("in.wav"), Path("out.wav"), 1.5)
        assert "--fine" in cmd
        assert "--centre-focus" in cmd
        assert "--crisp" not in cmd

    def test_auto_uses_r2_flags_on_legacy_rubberband(self, monkeypatch):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 1)
        cmd = build_stretch_command(Path("in.wav"), Path("out.wav"), 1.5)
        assert "--crisp" in cmd
        assert "--fine" not in cmd
        assert "--centre-focus" not in cmd

    def test_stretch_audio_invokes_built_command(self, monkeypatch, tmp_path):
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 4)
        calls = []

        def fake_run(cmd, capture_output, text):
            calls.append(cmd)
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr("breaks_machine.stretcher.subprocess.run", fake_run)

        input_path = tmp_path / "in.wav"
        input_path.touch()
        output_path = tmp_path / "out" / "out.wav"

        stretch_audio(input_path, output_path, ratio=0.5, engine="auto")

        assert len(calls) == 1
        assert calls[0][:3] == ["rubberband", "--fine", "--centre-focus"]
        assert calls[0][-2:] == [str(input_path), str(output_path)]


class TestStretchAudio:
    """Tests for audio stretching."""

    def test_stretch_creates_output(self, temp_audio_file, tmp_path):
        """Test that stretching creates an output file."""
        output_path = tmp_path / "stretched.wav"

        stretch_audio(temp_audio_file, output_path, ratio=1.5)

        assert output_path.exists()

    def test_stretch_changes_duration(self, temp_audio_file, tmp_path):
        """Test that stretching by 0.5 ratio roughly doubles duration."""
        output_path = tmp_path / "stretched.wav"

        # Get original duration
        original_info = sf.info(temp_audio_file)
        original_duration = original_info.duration

        # Stretch by 0.5 (half speed = double duration)
        stretch_audio(temp_audio_file, output_path, ratio=0.5)

        # Check new duration
        stretched_info = sf.info(output_path)
        stretched_duration = stretched_info.duration

        # Should be roughly 2x duration (allow 10% tolerance)
        assert abs(stretched_duration / original_duration - 2.0) < 0.2

    def test_stretch_preserves_sample_rate(self, temp_audio_file, tmp_path):
        """Test that stretching preserves sample rate."""
        output_path = tmp_path / "stretched.wav"

        original_info = sf.info(temp_audio_file)
        stretch_audio(temp_audio_file, output_path, ratio=1.5)
        stretched_info = sf.info(output_path)

        assert stretched_info.samplerate == original_info.samplerate


class TestStretchToBpm:
    """Tests for BPM-to-BPM stretching."""

    def test_stretch_to_bpm(self, temp_audio_file, tmp_path):
        """Test stretching from one BPM to another."""
        output_path = tmp_path / "stretched.wav"

        # Stretch from 120 to 90 (slower, longer)
        stretch_to_bpm(temp_audio_file, output_path, 120, 90)

        assert output_path.exists()

        # Duration should be source/target = 120/90 = 1.33x longer
        original_info = sf.info(temp_audio_file)
        stretched_info = sf.info(output_path)

        expected_ratio = 120 / 90  # ~1.33x longer
        actual_ratio = stretched_info.duration / original_info.duration

        assert abs(actual_ratio - expected_ratio) < 0.15
