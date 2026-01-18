"""Command-line interface for breaks-machine."""

from pathlib import Path

import click

from .processor import (
    ProcessingOptions,
    is_audio_file,
    parse_targets,
    process_directory,
    process_file,
)
from .stretcher import RubberbandNotFoundError, check_rubberband_installed


@click.group()
@click.version_option()
def cli():
    """breaks-machine: Time-stretch drum breaks to target BPMs."""
    pass


@cli.command()
@click.argument("input_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "-t",
    "--target",
    type=float,
    help="Single target BPM",
)
@click.option(
    "--targets",
    type=str,
    help="Comma-separated target BPMs (e.g., 90,120,140)",
)
@click.option(
    "-r",
    "--range",
    "range_spec",
    type=str,
    help="BPM range (e.g., 80-160)",
)
@click.option(
    "-s",
    "--step",
    type=int,
    default=10,
    show_default=True,
    help="Step size for range",
)
@click.option(
    "-b",
    "--bpm",
    type=float,
    help="Manual source BPM override",
)
@click.option(
    "-o",
    "--output",
    type=click.Path(path_type=Path),
    default=Path("./output"),
    show_default=True,
    help="Output directory",
)
@click.option(
    "--sample-rate",
    type=int,
    help="Target sample rate (e.g., 44100, 48000)",
)
@click.option(
    "--bit-depth",
    type=click.Choice(["16", "24"]),
    help="Target bit depth",
)
@click.option(
    "--mono",
    is_flag=True,
    help="Convert to mono",
)
@click.option(
    "-w",
    "--warn",
    is_flag=True,
    help="Warn if detected BPM differs from filename",
)
@click.option(
    "--crispness",
    type=click.IntRange(0, 6),
    default=5,
    show_default=True,
    help="Rubberband crispness (0-6, higher preserves transients)",
)
def stretch(
    input_path: Path,
    target: float | None,
    targets: str | None,
    range_spec: str | None,
    step: int,
    bpm: float | None,
    output: Path,
    sample_rate: int | None,
    bit_depth: str | None,
    mono: bool,
    warn: bool,
    crispness: int,
):
    """
    Time-stretch audio file(s) to target BPM(s).

    INPUT_PATH can be a single audio file or a directory containing audio files.

    Examples:

        # Single file, single target
        breaks-machine stretch break.wav --target 140

        # Multiple targets
        breaks-machine stretch break.wav --targets 90,120,140

        # Range of targets
        breaks-machine stretch break.wav --range 80-160 --step 10

        # Batch process directory
        breaks-machine stretch ./breaks/ --target 140

        # With format conversion
        breaks-machine stretch break.wav -t 140 --sample-rate 44100 --mono
    """
    # Check rubberband is installed
    try:
        check_rubberband_installed()
    except RubberbandNotFoundError as e:
        raise click.ClickException(str(e)) from None

    # Parse targets
    try:
        target_bpms = parse_targets(target, targets, range_spec, step)
    except ValueError as e:
        raise click.ClickException(str(e)) from None

    # Build options
    options = ProcessingOptions(
        manual_bpm=bpm,
        sample_rate=sample_rate,
        bit_depth=int(bit_depth) if bit_depth else None,
        mono=mono,
        warn=warn,
        crispness=crispness,
    )

    click.echo(f"Target BPM(s): {', '.join(str(int(t)) for t in target_bpms)}")
    click.echo(f"Output directory: {output}")
    click.echo()

    try:
        if input_path.is_dir():
            outputs = process_directory(
                input_path,
                target_bpms,
                output,
                options,
                echo=click.echo,
            )
        elif is_audio_file(input_path):
            outputs = process_file(
                input_path,
                target_bpms,
                output,
                options,
                echo=click.echo,
            )
        else:
            raise click.ClickException(
                f"Unsupported file type: {input_path.suffix}. Supported: .wav, .flac"
            )
    except Exception as e:
        raise click.ClickException(str(e)) from None

    click.echo()
    click.echo(f"Created {len(outputs)} file(s)")


def main():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    main()
