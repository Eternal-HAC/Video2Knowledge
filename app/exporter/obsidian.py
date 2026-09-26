"""Local Markdown exporter.

Stage 1 writes Obsidian-compatible Markdown files locally. It does not call any
Obsidian API or plugin.
"""

from __future__ import annotations

import os
from pathlib import Path

from app.markdown_writer import slugify_title


def export_markdown(markdown: str, title: str, output_dir: Path | str) -> Path:
    """Write Markdown to output_dir and return the created path.

    Existing files are never overwritten: the normalized base name is used
    first, and on collision a stable ``-2``, ``-3``, ... suffix is appended.
    Each candidate is created with exclusive semantics (``O_CREAT | O_EXCL``),
    so there is no check-then-write race window. The returned path is the file
    actually written; a write failure propagates without reporting success.
    """

    directory = Path(output_dir)
    directory.mkdir(parents=True, exist_ok=True)
    base_name = slugify_title(title)
    candidate = directory / f"{base_name}.md"
    counter = 2
    while True:
        try:
            _write_new_file(candidate, markdown)
        except FileExistsError:
            candidate = directory / f"{base_name}-{counter}.md"
            counter += 1
            continue
        return candidate


def _write_new_file(path: Path, content: str) -> None:
    """Create ``path`` exclusively and write ``content`` as UTF-8 text."""

    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL)
    try:
        handle = os.fdopen(fd, "w", encoding="utf-8")
    except OSError:
        os.close(fd)
        _remove_partial_output(path)
        raise
    try:
        with handle:
            handle.write(content)
    except OSError:
        _remove_partial_output(path)
        raise


def _remove_partial_output(path: Path) -> None:
    """Best-effort removal of a partial file this call exclusively created."""

    try:
        path.unlink()
    except OSError:
        pass
