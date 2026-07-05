"""Command-line interface for the Video2Knowledge Mock MVP."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from app.errors import MetadataProviderError, ProviderNotImplementedError
from app.pipeline import ImportPipelineOptions, run_import_pipeline


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="Video2Knowledge",
        description="Local First video-to-knowledge Mock pipeline.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    import_url = subparsers.add_parser(
        "import-url",
        help="Run the Mock import pipeline for a video URL.",
    )
    import_url.add_argument("url", help="Video URL to process with Mock data.")
    import_url.add_argument(
        "--output-dir",
        default="output/markdown",
        help="Directory for generated Markdown files.",
    )
    import_url.add_argument(
        "--metadata-provider",
        choices=["mock", "yt-dlp"],
        default="mock",
        help="Metadata provider to use. Only mock is implemented.",
    )
    import_url.add_argument(
        "--transcript-provider",
        choices=["mock", "real-fallback"],
        default="mock",
        help="Transcript provider to use. Only mock is implemented.",
    )
    return parser


def run_import_url(
    url: str,
    output_dir: Path | str,
    metadata_provider: str = "mock",
    transcript_provider: str = "mock",
) -> Path:
    result = run_import_pipeline(
        url,
        ImportPipelineOptions(
            output_dir=output_dir,
            metadata_provider=metadata_provider,
            transcript_provider=transcript_provider,
        ),
    )
    return result.output_path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "import-url":
        try:
            output_path = run_import_url(
                args.url,
                args.output_dir,
                metadata_provider=args.metadata_provider,
                transcript_provider=args.transcript_provider,
            )
        except (MetadataProviderError, ProviderNotImplementedError, ValueError) as error:
            print(f"Error: {error}", file=sys.stderr)
            return 1
        print(f"Generated Markdown: {output_path}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
