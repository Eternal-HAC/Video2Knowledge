"""Command-line interface for the Video2Knowledge Mock MVP."""

from __future__ import annotations

import argparse
from pathlib import Path

from app.downloader import get_mock_metadata
from app.exporter.obsidian import export_markdown
from app.markdown_writer import render_markdown
from app.summarizer import summarize_mock
from app.transcript import get_mock_transcript


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
    return parser


def run_import_url(url: str, output_dir: Path | str) -> Path:
    metadata = get_mock_metadata(url)
    transcript = get_mock_transcript(metadata)
    summary = summarize_mock(metadata, transcript)
    markdown = render_markdown(metadata, transcript, summary)
    return export_markdown(markdown, metadata.title, output_dir)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "import-url":
        output_path = run_import_url(args.url, args.output_dir)
        print(f"Generated Markdown: {output_path}")
        return 0

    parser.error(f"Unknown command: {args.command}")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())

