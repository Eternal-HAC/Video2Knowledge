"""Structured Markdown rendering for Video2Knowledge."""

from __future__ import annotations

from datetime import datetime, timezone
from importlib import resources
from pathlib import Path

from app.models import Summary, TranscriptSegment, VideoMetadata


DEFAULT_TEMPLATE_PACKAGE = "app.templates"
DEFAULT_TEMPLATE_NAME = "video_note.md.j2"


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
    rendered = template
    for key, value in context.items():
        rendered = rendered.replace("{{ " + key + " }}", value)
    return rendered


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
    }
    context = {key: _as_text(value) for key, value in yaml_sources.items()}
    for key, value in yaml_sources.items():
        context[f"{key}_yaml"] = _format_yaml_scalar(value)
    context.update(
        {
            "tags": _format_yaml_list(metadata.tags),
            "description": _format_yaml_block(metadata.description),
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


def _format_yaml_scalar(value: object) -> str:
    """Serialize one value as a YAML 1.1/1.2 compatible scalar.

    Strings are emitted double-quoted with the few escapes YAML defines, so
    colons, hashes, quotes, newlines, Unicode, and values that merely look
    like booleans, nulls, dates, or numbers keep their string type. ``None``
    becomes the plain ``null`` scalar.
    """

    if value is None:
        return "null"
    if not isinstance(value, str):
        value = str(value)
    escaped: list[str] = []
    for char in value:
        if char == "\\":
            escaped.append("\\\\")
        elif char == '"':
            escaped.append('\\"')
        elif char == "\n":
            escaped.append("\\n")
        elif char == "\r":
            escaped.append("\\r")
        elif char == "\t":
            escaped.append("\\t")
        elif ord(char) < 0x20 or ord(char) == 0x7F:
            escaped.append(f"\\x{ord(char):02X}")
        else:
            escaped.append(char)
    return '"' + "".join(escaped) + '"'


def _format_yaml_list(items: list[str]) -> str:
    """Serialize a list of scalars as a YAML flow sequence, empty as ``[]``."""

    return "[" + ", ".join(_format_yaml_scalar(item) for item in items) + "]"


def _format_yaml_block(value: str) -> str:
    """Indent every line of a string for a ``|-`` block scalar.

    The block scalar form keeps multi-line text readable while remaining safe
    for arbitrary content: every line is indented, so no input line can break
    out of the frontmatter value.
    """

    text = _as_text(value)
    if not text:
        return "  "
    return "\n".join(f"  {line}" if line else "  " for line in text.splitlines())


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _format_transcript(segments: list[TranscriptSegment]) -> str:
    return "\n".join(
        f"- [{segment.start} - {segment.end}] {segment.text}" for segment in segments
    )
