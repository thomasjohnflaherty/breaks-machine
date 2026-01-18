"""Tests for audio stretching."""

import soundfile as sf

from breaks_machine.stretcher import (
    calculate_stretch_ratio,
    check_rubberband_installed,
    stretch_audio,
    stretch_to_bpm,
)


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
