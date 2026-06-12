"""Tests for audio format conversion."""

import numpy as np
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

    def test_mono_downmix_overflow_normalized(self, tmp_path):
        """Test that hot float input downmixes to 16-bit without wraparound."""
        sr = 44100
        t = np.linspace(0, 0.1, int(sr * 0.1), endpoint=False)
        sig = 1.5 * np.sin(2 * np.pi * 440 * t)
        input_path = tmp_path / "hot_stereo.wav"
        sf.write(input_path, np.column_stack([sig, sig]), sr, subtype="FLOAT")

        output_path = tmp_path / "mono16.wav"
        convert_audio(input_path, output_path, bit_depth=16, mono=True)

        y, _ = sf.read(output_path)
        assert y.ndim == 1
        assert np.max(np.abs(y)) <= 1.0
        assert np.corrcoef(y, sig / 1.5)[0, 1] > 0.999

    def test_pcm16_output_is_dithered(self, tmp_path):
        """Test that float-to-16-bit conversion applies TPDF dither."""
        sr = 44100
        rng = np.random.default_rng(42)
        sig = rng.uniform(-0.5, 0.5, sr // 10)
        input_path = tmp_path / "float_in.wav"
        sf.write(input_path, sig, sr, subtype="FLOAT")

        output_path = tmp_path / "out16.wav"
        convert_audio(input_path, output_path, bit_depth=16)

        ref_path = tmp_path / "ref16.wav"
        stored_float, _ = sf.read(input_path)
        sf.write(ref_path, stored_float, sr, subtype="PCM_16")

        written, _ = sf.read(output_path, dtype="int16")
        undithered, _ = sf.read(ref_path, dtype="int16")
        diff = written.astype(np.int32) - undithered.astype(np.int32)
        assert np.any(diff != 0)
        assert np.max(np.abs(diff)) <= 2

    def test_pcm24_output_not_dithered(self, tmp_path):
        """Test that 24-bit output is written without dither."""
        sr = 44100
        rng = np.random.default_rng(7)
        sig = rng.uniform(-0.5, 0.5, sr // 10)
        input_path = tmp_path / "float_in.wav"
        sf.write(input_path, sig, sr, subtype="FLOAT")

        output_path = tmp_path / "out24.wav"
        convert_audio(input_path, output_path, bit_depth=24)

        ref_path = tmp_path / "ref24.wav"
        stored_float, _ = sf.read(input_path)
        sf.write(ref_path, stored_float, sr, subtype="PCM_24")

        written, _ = sf.read(output_path, dtype="int32")
        reference, _ = sf.read(ref_path, dtype="int32")
        assert np.array_equal(written, reference)

    def test_noop_conversion_copies_byte_for_byte(self, temp_audio_file, tmp_path):
        """Test that a no-op conversion to a new path copies without re-encoding."""
        output_path = tmp_path / "copy.wav"
        convert_audio(temp_audio_file, output_path, sample_rate=44100, bit_depth=16, mono=True)
        assert output_path.read_bytes() == temp_audio_file.read_bytes()

    def test_noop_conversion_in_place_untouched(self, temp_audio_file):
        """Test that an in-place no-op conversion leaves the file untouched."""
        before = temp_audio_file.read_bytes()
        convert_audio(temp_audio_file, bit_depth=16)
        assert temp_audio_file.read_bytes() == before


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
