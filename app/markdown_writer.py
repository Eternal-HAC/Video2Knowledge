"""Structured Markdown rendering for Video2Knowledge."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

from app.models import Summary, TranscriptSegment, VideoMetadata


DEFAULT_TEMPLATE_PACKAGE = "app.templates"
DEFAULT_TEMPLATE_NAME = "video_note.md.j2"
_PLACEHOLDER_PATTERN = re.compile(r"\{\{\s*([A-Za-z_][A-Za-z0-9_]*)\s*\}\}")


def render_markdown(
    metadata: VideoMetadata,
    transcript: list[TranscriptSegment],
    summary: Summary,
    template_path: Path | str | None = None,
) -> str:
    """Render a structured Markdown note using a tiny local template renderer.

    When ``template_path`` is ``None`` the packaged default template is loaded
    through :mod:`importlib.resources`, so rendering does not depend on the
    current working directory. An explicit ``template_path`` is read verbatim
    and must exist; a missing or unreadable custom template raises the
    corresponding ``OSError`` instead of silently falling back to the default.
    """

    template = _read_template(template_path)
    context = _build_context(metadata, summary, transcript)
    return _render_template_once(template, context)


def _build_context(
    metadata: VideoMetadata,
    summary: Summary,
    transcript: list[TranscriptSegment],
) -> dict[str, str]:
    yaml_sources: dict[str, object] = {
        "title": metadata.title,
        "platform": metadata.platform,
        "source_url": metadata.source_url,
        "canonical_url": metadata.canonical_url,
        "source_id": metadata.source_id,
        "author": metadata.author,
        "channel_id": metadata.channel_id,
        "published_at": metadata.published_at,
        "imported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "duration": metadata.duration,
        "language": metadata.language,
        "thumbnail_url": metadata.thumbnail_url,
        "status": metadata.status,
        "description": metadata.description,
    }
    context = {key: _as_text(value) for key, value in yaml_sources.items()}
    for key, value in yaml_sources.items():
        context[f"{key}_yaml"] = _format_yaml_scalar(value)
    context.update(
        {
            "tags": _format_yaml_list(metadata.tags),
            "one_sentence_summary": summary.one_sentence_summary,
            "core_ideas": _format_bullets(summary.core_ideas),
            "knowledge_points": _format_bullets(summary.knowledge_points),
            "technical_terms": _format_bullets(summary.technical_terms),
            "action_items": _format_bullets(summary.action_items),
            "transcript": _format_transcript(transcript),
        }
    )
    return context


def slugify_title(title: str) -> str:
    """Create a filesystem-friendly ASCII fallback slug."""

    chars = []
    for char in title.lower():
        if char.isalnum():
            chars.append(char)
        elif char in {" ", "-", "_"}:
            chars.append("-")
    slug = "".join(chars).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "video-note"


def _read_template(template_path: Path | str | None) -> str:
    if template_path is None:
        return (
            resources.files(DEFAULT_TEMPLATE_PACKAGE)
            .joinpath(DEFAULT_TEMPLATE_NAME)
            .read_text(encoding="utf-8")
        )
    return Path(template_path).read_text(encoding="utf-8")


def _as_text(value: object) -> str:
    return "" if value is None else str(value)


def _render_template_once(template: str, context: dict[str, str]) -> str:
    """Replace placeholders from the original template exactly once.

    Values inserted from metadata or generated content are returned directly
    by the callback and are never scanned again as template syntax.
    """

    def replace(match: re.Match[str]) -> str:
        key = match.group(1)
        return context.get(key, match.group(0))

    return _PLACEHOLDER_PATTERN.sub(replace, template)


def _format_yaml_scalar(value: object) -> str:
    """Serialize one value as a JSON-style string accepted by YAML parsers.

    JSON's quoted-string syntax is compatible with YAML double-quoted scalars.
    JSON escapes cover quotes, backslashes, and C0 controls; YAML-sensitive C1
    controls, Unicode line separators, and lone surrogates receive explicit
    ``\\u`` escapes. Other Unicode, including non-BMP characters, stays literal
    so YAML parsers do not expose JSON surrogate pairs as two code points.
    ``None`` is represented by YAML/JSON ``null``.
    """

    if value is None:
        return "null"
    if not isinstance(value, str):
        value = str(value)
    escaped: list[str] = []
    for char in value:
        codepoint = ord(char)
        if char in {'"', "\\"} or codepoint < 0x20:
            escaped.append(json.dumps(char, ensure_ascii=True)[1:-1])
        elif (
            0x7F <= codepoint <= 0x9F
            or codepoint in {0x2028, 0x2029}
            or 0xD800 <= codepoint <= 0xDFFF
        ):
            escaped.append(f"\\u{codepoint:04X}")
        else:
            escaped.append(char)
    return '"' + "".join(escaped) + '"'


def _format_yaml_list(items: list[str]) -> str:
    """Serialize a list of scalars as a YAML flow sequence, empty as ``[]``."""

    return "[" + ", ".join(_format_yaml_scalar(item) for item in items) + "]"


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _format_transcript(segments: list[TranscriptSegment]) -> str:
    return "\n".join(
        f"- [{segment.start} - {segment.end}] {segment.text}" for segment in segments
    )
