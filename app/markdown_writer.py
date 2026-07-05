"""Structured Markdown rendering for Video2Knowledge."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.models import Summary, TranscriptSegment, VideoMetadata


DEFAULT_TEMPLATE_PATH = Path("templates/video_note.md.j2")


def render_markdown(
    metadata: VideoMetadata,
    transcript: list[TranscriptSegment],
    summary: Summary,
    template_path: Path | str = DEFAULT_TEMPLATE_PATH,
) -> str:
    """Render a structured Markdown note using a tiny local template renderer."""

    template = Path(template_path).read_text(encoding="utf-8")
    context = {
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
        "tags": _format_yaml_list(metadata.tags),
        "status": metadata.status,
        "description": _format_yaml_block(metadata.description),
        "one_sentence_summary": summary.one_sentence_summary,
        "core_ideas": _format_bullets(summary.core_ideas),
        "knowledge_points": _format_bullets(summary.knowledge_points),
        "technical_terms": _format_bullets(summary.technical_terms),
        "action_items": _format_bullets(summary.action_items),
        "transcript": _format_transcript(transcript),
    }

    rendered = template
    for key, value in context.items():
        rendered = rendered.replace("{{ " + key + " }}", value)
    return rendered


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


def _format_yaml_list(items: list[str]) -> str:
    quoted = [f'"{item}"' for item in items]
    return "[" + ", ".join(quoted) + "]"


def _format_yaml_block(value: str) -> str:
    if not value:
        return "  "
    return "\n".join(f"  {line}" if line else "  " for line in value.splitlines())


def _format_bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _format_transcript(segments: list[TranscriptSegment]) -> str:
    return "\n".join(
        f"- [{segment.start} - {segment.end}] {segment.text}" for segment in segments
    )
