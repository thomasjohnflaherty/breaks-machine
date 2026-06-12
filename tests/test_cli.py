"""Tests for the CLI."""

import pytest
from click.testing import CliRunner

from breaks_machine.cli import cli


@pytest.fixture
def runner():
    """Create a CLI test runner."""
    return CliRunner()


class TestCliStretch:
    """Tests for the stretch command."""

    def test_help(self, runner):
        """Test that help works."""
        result = runner.invoke(cli, ["stretch", "--help"])
        assert result.exit_code == 0
        assert "Time-stretch audio file" in result.output

    def test_default_mode_is_hybrid(self, runner):
        """Help output advertises hybrid as the default mode."""
        result = runner.invoke(cli, ["stretch", "--help"])
        assert result.exit_code == 0
        assert "[default: hybrid]" in result.output

    def test_version(self, runner):
        """Test that version works."""
        result = runner.invoke(cli, ["--version"])
        assert result.exit_code == 0

    def test_no_target_error(self, runner, temp_audio_file):
        """Test that missing target BPM gives error."""
        result = runner.invoke(cli, ["stretch", str(temp_audio_file)])
        assert result.exit_code != 0
        assert "No target BPM specified" in result.output

    def test_single_target(self, runner, temp_audio_file_170bpm, tmp_path):
        """Test stretching to a single target BPM."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--target",
                "120",
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Created 1 file" in result.output

        expected_output = output_dir / "amen_170" / "amen_120.wav"
        assert expected_output.exists()

    def test_multiple_targets(self, runner, temp_audio_file_170bpm, tmp_path):
        """Test stretching to multiple target BPMs."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--targets",
                "90,120,140",
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Created 3 file" in result.output

    def test_range_targets(self, runner, temp_audio_file_170bpm, tmp_path):
        """Test stretching to a range of target BPMs."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--range",
                "100-130",
                "--step",
                "10",
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        # 100, 110, 120, 130 = 4 files
        assert "Created 4 file" in result.output

    def test_manual_bpm_override(self, runner, temp_audio_file, tmp_path):
        """Test manual BPM override."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file),
                "--target",
                "90",
                "--bpm",
                "120",  # Override source BPM
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

    def test_mono_conversion(self, runner, temp_stereo_file, tmp_path):
        """Test mono conversion flag."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_stereo_file),
                "--target",
                "120",
                "--bpm",
                "100",
                "--mono",
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"

    def test_engine_r2(self, runner, temp_audio_file_170bpm, tmp_path):
        """Test forcing the legacy R2 engine."""
        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--target",
                "120",
                "--engine",
                "r2",
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Created 1 file" in result.output

    def test_engine_r3_requires_rubberband_3(
        self, runner, temp_audio_file_170bpm, tmp_path, monkeypatch
    ):
        """Forcing r3 with rubberband < 3 should error clearly."""
        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 2)

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--target",
                "120",
                "--engine",
                "r3",
                "--output",
                str(tmp_path / "output"),
            ],
        )

        assert result.exit_code != 0
        assert "requires rubberband >= 3" in result.output

    def test_invalid_engine(self, runner, temp_audio_file_170bpm):
        """Invalid engine choice should be rejected."""
        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--target",
                "120",
                "--engine",
                "r4",
            ],
        )

        assert result.exit_code != 0

    def test_mode_repitch(self, runner, temp_audio_file_170bpm, tmp_path):
        """Repitch mode creates a file with vinyl-style duration."""
        import soundfile as sf

        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--target",
                "90",
                "--mode",
                "repitch",
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        expected_output = output_dir / "amen_170" / "amen_90.wav"
        assert expected_output.exists()
        assert abs(sf.info(expected_output).duration - 170 / 90) < 0.02

    def test_mode_slice(self, runner, temp_audio_file_170bpm, tmp_path):
        """Slice mode creates a re-spaced file without rubberband."""
        import soundfile as sf

        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--target",
                "90",
                "--mode",
                "slice",
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        expected_output = output_dir / "amen_170" / "amen_90.wav"
        assert expected_output.exists()
        assert abs(sf.info(expected_output).duration - 170 / 90) < 0.02

    def test_mode_hybrid(self, runner, temp_audio_file_170bpm, tmp_path, monkeypatch):
        """Hybrid mode stretches the residual factor after repitching."""
        import shutil
        import subprocess

        monkeypatch.setattr("breaks_machine.stretcher.get_rubberband_major_version", lambda: 4)

        commands = []

        def fake_run(cmd, capture_output, text):
            commands.append(cmd)
            shutil.copy(cmd[-2], cmd[-1])
            return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")

        monkeypatch.setattr("breaks_machine.stretcher.subprocess.run", fake_run)

        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--target",
                "90",
                "--mode",
                "hybrid",
                "--max-semitones",
                "3.0",
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert (output_dir / "amen_170" / "amen_90.wav").exists()
        assert len(commands) == 1
        tempo = float(commands[0][commands[0].index("--tempo") + 1])
        assert abs(tempo - (90 / 170) / 2 ** (-3 / 12)) < 0.001

    def test_invalid_mode(self, runner, temp_audio_file_170bpm):
        """Invalid mode choice should be rejected."""
        result = runner.invoke(
            cli,
            [
                "stretch",
                str(temp_audio_file_170bpm),
                "--target",
                "90",
                "--mode",
                "warp",
            ],
        )

        assert result.exit_code != 0

    def test_unsupported_format(self, runner, tmp_path):
        """Test that unsupported formats give error."""
        fake_file = tmp_path / "test.mp3"
        fake_file.touch()

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(fake_file),
                "--target",
                "120",
            ],
        )

        assert result.exit_code != 0
        assert "Unsupported file type" in result.output


class TestCliDirectory:
    """Tests for directory batch processing."""

    def test_batch_directory(self, runner, temp_audio_file_170bpm, tmp_path):
        """Test processing a directory of files."""
        # Create a directory with the test file
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        # Copy the test file to the input directory
        import shutil

        shutil.copy(temp_audio_file_170bpm, input_dir / "amen_170.wav")

        output_dir = tmp_path / "output"

        result = runner.invoke(
            cli,
            [
                "stretch",
                str(input_dir),
                "--target",
                "120",
                "--output",
                str(output_dir),
            ],
        )

        assert result.exit_code == 0, f"CLI failed: {result.output}"
        assert "Created 1 file" in result.output
