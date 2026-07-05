"""Local Markdown exporter.

Stage 1 writes Obsidian-compatible Markdown files locally. It does not call any
Obsidian API or plugin.
"""

from __future__ import annotations

from pathlib import Path

from app.markdown_writer import slugify_title


def export_markdown(markdown: str, title: str, output_dir: Path | str) -> Path:
    """Write Markdown to output_dir and return the created path."""

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{slugify_title(title)}.md"
    path.write_text(markdown, encoding="utf-8")
    return path

