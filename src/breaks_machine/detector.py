"""BPM detection from filenames and audio analysis."""

import re
from collections.abc import Callable
from pathlib import Path

import librosa


class BPMDetectionError(Exception):
    """Raised when BPM cannot be determined."""

    pass


def parse_bpm_from_filename(file_path: Path) -> float | None:
    """
    Extract BPM from filename using common naming conventions.

    Matches patterns like:
    - amen_170.wav -> 170
    - 164_HT_Drums.wav -> 164
    - break-140bpm.flac -> 140
    - think_120_BPM.wav -> 120
    - funky_90-bpm.wav -> 90
    - drum_loop_140BPM.wav -> 140

    Returns None if no BPM found in filename.
    """
    filename = file_path.stem

    # Pattern: number followed by optional separator and "bpm" (case insensitive)
    # e.g., "140bpm", "140-bpm", "140_BPM", "140 bpm"
    pattern_with_bpm = r"(\d{2,3})[\s_-]?bpm"
    match = re.search(pattern_with_bpm, filename, re.IGNORECASE)
    if match:
        bpm = float(match.group(1))
        if 90 <= bpm <= 180:
            return bpm

    # Pattern: 2-3 digit number at start followed by separator
    # e.g., "164_HT_Drums", "120-break"
    pattern_leading = r"^(\d{2,3})[\s_-]"
    match = re.match(pattern_leading, filename)
    if match:
        bpm = float(match.group(1))
        if 90 <= bpm <= 180:
            return bpm

    # Pattern: underscore/hyphen followed by 2-3 digit number at end or before extension
    # e.g., "amen_170", "break-140"
    pattern_trailing = r"[_-](\d{2,3})(?:[_-]|$)"
    match = re.search(pattern_trailing, filename)
    if match:
        bpm = float(match.group(1))
        if 90 <= bpm <= 180:
            return bpm

    return None


def detect_bpm_with_librosa(file_path: Path) -> float:
    """
    Detect BPM using librosa's beat tracking with multiple strategies.

    Uses multiple tempo priors and subdivision correction to improve accuracy
    on complex breakbeats.

    Returns the estimated BPM.
    """
    y, sr = librosa.load(file_path, sr=None)

    # Strategy 1: Try multiple starting priors
    # Default (120), medium (140), and high (170) to cover different tempo ranges
    priors = [None, 140, 170]
    all_candidates = []

    for prior in priors:
        if prior is None:
            tempo = librosa.feature.tempo(y=y, sr=sr, aggregate=None)
        else:
            tempo = librosa.feature.tempo(y=y, sr=sr, start_bpm=prior, aggregate=None)

        # Extract candidates
        if hasattr(tempo, "__len__") and len(tempo) > 0:
            all_candidates.extend([float(t) for t in tempo[:4]])
        else:
            all_candidates.append(float(tempo))

    # Remove duplicates
    candidates = sorted(set(all_candidates))

    # Strategy 2: For each candidate, consider common subdivision relationships
    # Breakbeat detection often finds subdivisions (2/3, 1/2, 3/4 time)
    expanded_candidates = []
    for bpm in candidates:
        expanded_candidates.append(bpm)
        expanded_candidates.append(bpm * 2)  # Double-time (2x)
        expanded_candidates.append(bpm * 1.5)  # 3/2 time
        expanded_candidates.append(bpm * (4 / 3))  # 4/3 time
        expanded_candidates.append(bpm / 1.5)  # 2/3 time (detected too high)

    # Remove duplicates and filter to reasonable range (80-200 BPM)
    valid_candidates = sorted(set(bpm for bpm in expanded_candidates if 80 <= bpm <= 200))

    if not valid_candidates:
        # Fallback to original candidate if nothing in range
        return candidates[0] if candidates else 120.0

    # Strategy 3: Prefer direct detections over derived subdivisions
    # Group candidates by how they were obtained
    direct_detections = [bpm for bpm in candidates if 80 <= bpm <= 200]

    if direct_detections:
        # Prefer candidates that were directly detected (not subdivisions)
        # Return the one closest to the common breakbeat range (140-180)
        target = 160
        best = min(direct_detections, key=lambda x: abs(x - target))
        return best
    else:
        # Fall back to derived candidates if no direct detection in range
        target = 160
        best = min(valid_candidates, key=lambda x: abs(x - target))
        return best


def bpms_match(bpm1: float, bpm2: float, tolerance: float = 3.0) -> bool:
    """
    Check if two BPMs match, accounting for 2x/0.5x detection differences.

    Args:
        bpm1: First BPM value
        bpm2: Second BPM value
        tolerance: Acceptable difference in BPM (default 3.0)

    Returns:
        True if BPMs match (including half/double time variants)
    """
    # Direct match
    if abs(bpm1 - bpm2) <= tolerance:
        return True

    # Check half time (bpm2 is half of bpm1)
    if abs(bpm1 - bpm2 * 2) <= tolerance:
        return True

    # Check double time (bpm2 is double of bpm1)
    if abs(bpm1 * 2 - bpm2) <= tolerance:
        return True

    return False


def get_source_bpm(
    file_path: Path,
    manual_bpm: float | None = None,
    warn: bool = False,
    warn_callback: Callable[[str], None] | None = None,
) -> float:
    """
    Determine source BPM using priority: manual > filename > auto-detect.

    Args:
        file_path: Path to audio file
        manual_bpm: User-specified BPM override (highest priority)
        warn: Whether to warn if detected BPM differs from filename
        warn_callback: Function to call with warning message

    Returns:
        Detected or specified BPM

    Raises:
        BPMDetectionError: If no BPM source available
    """
    # 1. Manual override wins
    if manual_bpm is not None:
        return manual_bpm

    # 2. Try filename parsing
    filename_bpm = parse_bpm_from_filename(file_path)

    # 3. Auto-detect as fallback (or for validation)
    detected_bpm = None
    if filename_bpm is None or warn:
        try:
            detected_bpm = detect_bpm_with_librosa(file_path)
        except Exception as e:
            if filename_bpm is None:
                raise BPMDetectionError(f"Could not determine BPM for {file_path}: {e}") from e

    # Return filename BPM if available
    if filename_bpm is not None:
        # Warn if detection differs (ignoring 2x/0.5x)
        if warn and detected_bpm is not None and warn_callback:
            if not bpms_match(filename_bpm, detected_bpm):
                warn_callback(
                    f"Filename suggests {filename_bpm} BPM, but detected {detected_bpm:.1f} BPM"
                )
        return filename_bpm

    # Fall back to detected BPM
    if detected_bpm is not None:
        return detected_bpm

    raise BPMDetectionError(f"Could not determine BPM for {file_path}")
