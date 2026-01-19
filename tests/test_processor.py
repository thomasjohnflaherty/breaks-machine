"""Tests for processing pipeline."""

from pathlib import Path

import pytest

from breaks_machine.processor import (
    ProcessingOptions,
    generate_output_path,
    is_audio_file,
    parse_targets,
)


class TestIsAudioFile:
    """Tests for audio file detection."""

    def test_wav_file(self, temp_audio_file):
        """Test that .wav files are recognized."""
        assert is_audio_file(temp_audio_file) is True

    def test_flac_file(self, tmp_path):
        """Test that .flac files are recognized."""
        flac_path = tmp_path / "test.flac"
        flac_path.touch()
        assert is_audio_file(flac_path) is True

    def test_unsupported_format(self, tmp_path):
        """Test that unsupported formats are rejected."""
        mp3_path = tmp_path / "test.mp3"
        mp3_path.touch()
        assert is_audio_file(mp3_path) is False

    def test_directory(self, tmp_path):
        """Test that directories are rejected."""
        assert is_audio_file(tmp_path) is False


class TestGenerateOutputPath:
    """Tests for output path generation."""

    def test_single_target(self):
        """Test output path for single target."""
        input_path = Path("/input/amen_170.wav")
        output_dir = Path("/output")

        result = generate_output_path(input_path, output_dir, 120)

        assert result == Path("/output/amen_170/amen_120.wav")

    def test_preserves_extension(self):
        """Test that original extension is preserved."""
        input_path = Path("/input/break.flac")
        output_dir = Path("/output")

        result = generate_output_path(input_path, output_dir, 90)

        assert result == Path("/output/break/break_90.flac")

    def test_float_bpm_truncated(self):
        """Test that float BPM is truncated to int."""
        input_path = Path("/input/test.wav")
        output_dir = Path("/output")

        result = generate_output_path(input_path, output_dir, 120.5)

        assert result == Path("/output/test/test_120.wav")


class TestParseTargets:
    """Tests for target BPM parsing."""

    def test_single_target(self):
        """Test parsing single target."""
        result = parse_targets(120, None, None, 10)
        assert result == [120.0]

    def test_multiple_targets(self):
        """Test parsing comma-separated targets."""
        result = parse_targets(None, "90,120,140", None, 10)
        assert result == [90.0, 120.0, 140.0]

    def test_range_targets(self):
        """Test parsing range specification."""
        result = parse_targets(None, None, "80-100", 10)
        assert result == [80.0, 90.0, 100.0]

    def test_combined_targets(self):
        """Test combining multiple target specifications."""
        result = parse_targets(75, "120,140", "200-220", 10)
        assert result == [75.0, 120.0, 140.0, 200.0, 210.0, 220.0]

    def test_removes_duplicates(self):
        """Test that duplicate targets are removed."""
        result = parse_targets(120, "120,140,120", None, 10)
        assert result == [120.0, 140.0]

    def test_no_targets_error(self):
        """Test that no targets raises error."""
        with pytest.raises(ValueError, match="No target BPM specified"):
            parse_targets(None, None, None, 10)

    def test_invalid_range_error(self):
        """Test that invalid range raises error."""
        with pytest.raises(ValueError, match="Invalid range format"):
            parse_targets(None, None, "80-100-120", 10)


class TestProcessingOptions:
    """Tests for ProcessingOptions dataclass."""

    def test_defaults(self):
        """Test default values."""
        options = ProcessingOptions()

        assert options.manual_bpm is None
        assert options.sample_rate is None
        assert options.bit_depth is None
        assert options.mono is False
        assert options.warn is False
        assert options.crispness == 5

    def test_custom_values(self):
        """Test custom values."""
        options = ProcessingOptions(
            manual_bpm=120,
            sample_rate=44100,
            bit_depth=16,
            mono=True,
            warn=True,
            crispness=6,
        )

        assert options.manual_bpm == 120
        assert options.sample_rate == 44100
        assert options.bit_depth == 16
        assert options.mono is True
        assert options.warn is True
        assert options.crispness == 6
