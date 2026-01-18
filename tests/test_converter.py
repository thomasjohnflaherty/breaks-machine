"""Tests for audio format conversion."""

import soundfile as sf

from breaks_machine.converter import convert_audio, get_audio_info


class TestConvertAudio:
    """Tests for audio format conversion."""

    def test_no_conversion_returns_same_file(self, temp_audio_file):
        """Test that no-op conversion returns the same path."""
        result = convert_audio(temp_audio_file)
        assert result == temp_audio_file

    def test_sample_rate_conversion(self, temp_audio_file, tmp_path):
        """Test sample rate conversion."""
        output_path = tmp_path / "resampled.wav"

        # Original is 44100 Hz
        original_info = sf.info(temp_audio_file)
        assert original_info.samplerate == 44100

        # Convert to 48000 Hz
        convert_audio(temp_audio_file, output_path, sample_rate=48000)

        converted_info = sf.info(output_path)
        assert converted_info.samplerate == 48000

    def test_mono_conversion(self, temp_stereo_file, tmp_path):
        """Test stereo to mono conversion."""
        output_path = tmp_path / "mono.wav"

        # Original is stereo
        original_info = sf.info(temp_stereo_file)
        assert original_info.channels == 2

        # Convert to mono
        convert_audio(temp_stereo_file, output_path, mono=True)

        converted_info = sf.info(output_path)
        assert converted_info.channels == 1

    def test_bit_depth_conversion(self, temp_audio_file, tmp_path):
        """Test bit depth conversion."""
        output_path = tmp_path / "24bit.wav"

        # Convert to 24-bit
        convert_audio(temp_audio_file, output_path, bit_depth=24)

        converted_info = sf.info(output_path)
        assert converted_info.subtype == "PCM_24"

    def test_combined_conversion(self, temp_stereo_file, tmp_path):
        """Test multiple conversions at once."""
        output_path = tmp_path / "converted.wav"

        convert_audio(
            temp_stereo_file,
            output_path,
            sample_rate=22050,
            bit_depth=16,
            mono=True,
        )

        converted_info = sf.info(output_path)
        assert converted_info.samplerate == 22050
        assert converted_info.channels == 1
        assert converted_info.subtype == "PCM_16"


class TestGetAudioInfo:
    """Tests for audio info retrieval."""

    def test_get_audio_info(self, temp_audio_file):
        """Test getting audio file info."""
        info = get_audio_info(temp_audio_file)

        assert info["sample_rate"] == 44100
        assert info["channels"] == 1
        assert info["format"] == "WAV"
        assert info["subtype"] == "PCM_16"
        assert info["duration"] > 0
        assert info["frames"] > 0
