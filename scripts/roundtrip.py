"""Round-trip fidelity analysis for breaks-machine stretch engines.

Mode "roundtrip": stretches source BPM -> target BPM, then back target ->
source, and compares the round-trip audio against the original to quantify
fidelity loss.

Mode "compare-renders": takes two already-rendered files (e.g. an old-pipeline
and a new-pipeline render at the same target BPM), stretches each BACK to the
source BPM with the same R3 engine, and scores both against the original
source. The shared R3 up-stretch cancels out of the comparison, so metric
differences are attributable to the engine used for the original down-stretch.

Usage:
    uv run python scripts/roundtrip.py roundtrip <input.wav> \\
        [--bpm 170] [--targets 160,150,140,130,120] [--engines r3,r2,hybrid]

    uv run python scripts/roundtrip.py compare-renders <source.wav> \\
        <rendered_old.wav> <rendered_new.wav> --target-bpm 140 [--bpm 170]
"""

import argparse
import sys
import tempfile
from pathlib import Path

import librosa
import numpy as np
import soundfile as sf
from scipy.signal import correlate

from breaks_machine.detector import get_source_bpm
from breaks_machine.repitch import hybrid_to_bpm
from breaks_machine.stretcher import stretch_to_bpm

N_FFT = 2048
HOP = 512
EPS = 1e-10
DB_FLOOR = 80.0
MAX_LAG_SECONDS = 0.25

LEGEND = """\
Metrics (original vs round-trip, mono-mixed, lag-aligned, length-matched):
  LSD (dB)   Log-spectral distance: RMS difference of dB magnitude spectra
             per frame (floored at peak-80 dB), averaged. 0 = identical;
             <1 dB barely audible, >3 dB clearly audible coloration.
             Lower is better.
  SpecConv   Spectral convergence: ||S_orig - S_rt||_F / ||S_orig||_F.
             0 = identical spectra; <0.1 very close, >0.5 heavily altered.
             Lower is better.
  OnsetCorr  Pearson r between onset-strength envelopes — transient
             preservation proxy. 1.0 = perfect; >0.9 good, <0.7 smeared
             transients. Higher is better.
  WaveCorr   Pearson r of waveforms after a fine cross-correlation alignment
             on top of the envelope alignment. Phase-vocoder output is not
             sample-aligned and phase rotates freely, so low values are
             expected and NOT necessarily audible — treat as informational
             and rely on the metrics above.
  lag        Coarse alignment offset (amplitude-envelope cross-correlation,
             +/-0.25 s window), in samples. Applied before all metrics.

Caveat: round-trip loss is roughly an UPPER BOUND of ~2x the single-pass
loss (two stretches are applied); single-pass fidelity is better than
these numbers suggest."""

COMPARE_CAVEAT = """\
Note: both renders were stretched back to the source BPM with the same R3
engine, so the shared up-stretch contributes equally to both rows — metric
differences are attributable to the engine used for the original
down-stretch, not to absolute single-pass fidelity."""


def render_roundtrip(
    input_path: Path,
    workdir: Path,
    engine: str,
    source_bpm: float,
    target_bpm: float,
) -> Path:
    forward = workdir / f"{engine}_{target_bpm:g}_fwd{input_path.suffix}"
    back = workdir / f"{engine}_{target_bpm:g}_rt{input_path.suffix}"

    if engine == "hybrid":
        hybrid_to_bpm(input_path, forward, source_bpm, target_bpm)
        hybrid_to_bpm(forward, back, target_bpm, source_bpm)
    else:
        stretch_to_bpm(input_path, forward, source_bpm, target_bpm, engine=engine)
        stretch_to_bpm(forward, back, target_bpm, source_bpm, engine=engine)
    return back


def load_mono(path: Path) -> tuple[np.ndarray, int]:
    y, sr = sf.read(path, dtype="float64")
    if y.ndim > 1:
        y = y.mean(axis=1)
    return y, sr


def match_length(a: np.ndarray, b: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    n = max(len(a), len(b))
    a = np.pad(a, (0, n - len(a)))
    b = np.pad(b, (0, n - len(b)))
    return a, b


def pearson(a: np.ndarray, b: np.ndarray) -> float:
    if a.std() == 0 or b.std() == 0:
        return float("nan")
    return float(np.corrcoef(a, b)[0, 1])


def find_lag(a: np.ndarray, b: np.ndarray, max_lag: int) -> int:
    xcorr = correlate(b, a, mode="full", method="fft")
    center = len(a) - 1
    window = xcorr[center - max_lag : center + max_lag + 1]
    return int(np.argmax(window) - max_lag)


def amplitude_envelope(y: np.ndarray, win: int = 256) -> np.ndarray:
    kernel = np.ones(win) / win
    return np.convolve(np.abs(y), kernel, mode="same")


def shift_align(a: np.ndarray, b: np.ndarray, lag: int) -> tuple[np.ndarray, np.ndarray]:
    if lag > 0:
        return a[: len(a) - lag], b[lag:]
    if lag < 0:
        return a[-lag:], b[: len(b) + lag]
    return a, b


def compute_metrics(orig: np.ndarray, rt: np.ndarray, sr: int) -> dict[str, float]:
    orig, rt = match_length(orig, rt)
    lag = find_lag(amplitude_envelope(orig), amplitude_envelope(rt), int(MAX_LAG_SECONDS * sr))
    orig, rt = shift_align(orig, rt, lag)

    s_orig = np.abs(librosa.stft(orig, n_fft=N_FFT, hop_length=HOP))
    s_rt = np.abs(librosa.stft(rt, n_fft=N_FFT, hop_length=HOP))

    floor = 20 * np.log10(max(s_orig.max(), s_rt.max()) + EPS) - DB_FLOOR
    db_orig = np.maximum(20 * np.log10(s_orig + EPS), floor)
    db_rt = np.maximum(20 * np.log10(s_rt + EPS), floor)
    lsd = float(np.mean(np.sqrt(np.mean((db_orig - db_rt) ** 2, axis=0))))

    spec_conv = float(np.linalg.norm(s_orig - s_rt) / (np.linalg.norm(s_orig) + EPS))

    env_orig = librosa.onset.onset_strength(S=librosa.amplitude_to_db(s_orig), sr=sr)
    env_rt = librosa.onset.onset_strength(S=librosa.amplitude_to_db(s_rt), sr=sr)
    onset_corr = pearson(env_orig, env_rt)

    fine_lag = find_lag(orig, rt, N_FFT)
    wave_corr = pearson(*shift_align(orig, rt, fine_lag))

    return {
        "lsd": lsd,
        "spec_conv": spec_conv,
        "onset_corr": onset_corr,
        "wave_corr": wave_corr,
        "lag": lag,
    }


def print_table(rows: list[dict], source_bpm: float, label_key: str = "engine") -> None:
    header = (
        f"{label_key:<8} {'target':>6} {'ratio':>6} {'LSD (dB)':>9} "
        f"{'SpecConv':>9} {'OnsetCorr':>10} {'WaveCorr':>9} {'lag':>6}"
    )
    print(header)
    print("-" * len(header))
    for r in rows:
        print(
            f"{r[label_key]:<8} {r['target']:>6g} {r['target'] / source_bpm:>6.3f} "
            f"{r['lsd']:>9.2f} {r['spec_conv']:>9.3f} {r['onset_corr']:>10.3f} "
            f"{r['wave_corr']:>9.3f} {r['lag']:>6d}"
        )


def load_matched(path: Path, sr: int) -> np.ndarray:
    y, y_sr = load_mono(path)
    if y_sr != sr:
        y = librosa.resample(y, orig_sr=y_sr, target_sr=sr)
    return y


def run_roundtrip(args: argparse.Namespace) -> None:
    if not args.input.exists():
        sys.exit(f"Input file not found: {args.input}")

    targets = [float(t) for t in args.targets.split(",")]
    engines = [e.strip().lower() for e in args.engines.split(",")]
    valid = {"r3", "r2", "hybrid"}
    if not set(engines) <= valid:
        sys.exit(f"Unknown engine(s): {set(engines) - valid}. Choose from {sorted(valid)}.")

    source_bpm = get_source_bpm(args.input, manual_bpm=args.bpm)
    orig, sr = load_mono(args.input)

    print(f"\nRound-trip fidelity: {args.input.name}")
    print(f"Source BPM: {source_bpm:g}  |  sr: {sr} Hz  |  duration: {len(orig) / sr:.2f}s\n")

    rows = []
    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        for engine in engines:
            for target in targets:
                rt_path = render_roundtrip(args.input, workdir, engine, source_bpm, target)
                rt = load_matched(rt_path, sr)
                metrics = compute_metrics(orig, rt, sr)
                rows.append({"engine": engine, "target": target, **metrics})

    print_table(rows, source_bpm)
    print()
    print(LEGEND)


def run_compare_renders(args: argparse.Namespace) -> None:
    renders = [("old", args.rendered_old), ("new", args.rendered_new)]
    for path in [args.source, *(p for _, p in renders)]:
        if not path.exists():
            sys.exit(f"File not found: {path}")

    source_bpm = get_source_bpm(args.source, manual_bpm=args.bpm)
    orig, sr = load_mono(args.source)

    print(f"\nRender comparison: {args.source.name} @ target {args.target_bpm:g} BPM")
    print(f"Source BPM: {source_bpm:g}  |  sr: {sr} Hz  |  duration: {len(orig) / sr:.2f}s")
    print(f"old: {args.rendered_old}")
    print(f"new: {args.rendered_new}\n")

    rows = []
    with tempfile.TemporaryDirectory() as tmpdir:
        workdir = Path(tmpdir)
        for label, path in renders:
            back = workdir / f"{label}_back{path.suffix}"
            stretch_to_bpm(path, back, args.target_bpm, source_bpm, engine="r3")
            rt = load_matched(back, sr)
            metrics = compute_metrics(orig, rt, sr)
            rows.append({"render": label, "target": args.target_bpm, **metrics})

    print_table(rows, source_bpm, label_key="render")
    print()
    print(COMPARE_CAVEAT)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="command", required=True)

    rt = sub.add_parser("roundtrip", help="Round-trip a source file through each engine")
    rt.add_argument("input", type=Path)
    rt.add_argument("--bpm", type=float, default=None, help="Source BPM override")
    rt.add_argument("--targets", default="160,150,140,130,120")
    rt.add_argument("--engines", default="r3,r2,hybrid")
    rt.set_defaults(func=run_roundtrip)

    cr = sub.add_parser(
        "compare-renders",
        help="Score two already-rendered files against the original source",
    )
    cr.add_argument("source", type=Path)
    cr.add_argument("rendered_old", type=Path)
    cr.add_argument("rendered_new", type=Path)
    cr.add_argument("--target-bpm", type=float, required=True)
    cr.add_argument("--bpm", type=float, default=None, help="Source BPM override")
    cr.set_defaults(func=run_compare_renders)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
