# Changelog

All notable changes to breaks-machine will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-01-20

### Added
- Leading BPM pattern detection in filenames (e.g., `164_HT_Drums.wav` → 164 BPM, `140_break.flac` → 140 BPM)
- Comprehensive documentation of all supported BPM filename patterns
- Troubleshooting section in README for BPM detection issues
- Clear guidance on recommended workflows (filename patterns vs auto-detection)

### Changed
- **Simplified output filename convention**: Changed from `basename_XXXbpm.ext` to `basename_XXX.ext` (e.g., `amen_170.wav @ 140 BPM` now outputs `amen_140.wav` instead of `amen_140bpm.wav`)
- **Tightened BPM detection range**: Narrowed from 50-250 BPM to 90-180 BPM to match typical breakbeat tempo range and reduce false positives
- Improved documentation clarity around auto-detection limitations - now explicitly states that auto-detection is experimental and filename patterns are recommended

### Fixed
- Documentation now accurately reflects auto-detection reliability issues
- BPM filename pattern examples now comprehensively documented

## [0.1.0] - 2026-01-19

### Added
- Initial release of breaks-machine
- Command-line tool for time-stretching drum breaks to target BPMs
- BPM detection from filename patterns (e.g., `amen_170.wav`, `break-140bpm.flac`)
- Multi-strategy librosa-based auto-detection with subdivision correction
- Rubberband integration with crispness=5 optimized for drums
- Multiple target modes: single BPM, multiple targets, and range with custom steps
- Batch processing for entire directories
- Format conversion options: sample rate, bit depth, and channel conversion
- Comprehensive test suite with 58 tests
- GitHub Actions CI/CD pipeline
- PyPI publishing automation
- Complete documentation and development setup

[0.2.0]: https://github.com/thomasjohnflaherty/breaks-machine/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/thomasjohnflaherty/breaks-machine/releases/tag/v0.1.0
