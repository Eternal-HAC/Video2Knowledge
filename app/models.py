"""Shared data structures for the Mock MVP pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoSource:
    raw_input: str
    source_type: str
    platform: str


@dataclass(frozen=True)
class PlatformCapabilities:
    supports_metadata: bool
    supports_transcript: bool
    supports_local_file: bool
    supports_cookies: bool
    supports_auth: bool
    metadata_providers: list[str]
    transcript_providers: list[str]


@dataclass(frozen=True)
class VideoMetadata:
    title: str
    platform: str
    source_url: str
    author: str
    published_at: str
    duration: str
    language: str
    tags: list[str]
    status: str
    source_id: str = ""
    canonical_url: str = ""
    thumbnail_url: str = ""
    description: str = ""
    raw_metadata: dict[str, str] | None = None


@dataclass(frozen=True)
class TranscriptSegment:
    start: str
    end: str
    text: str


@dataclass(frozen=True)
class TranscriptResult:
    segments: list[TranscriptSegment]
    provider: str
    attempted_providers: list[str]


@dataclass(frozen=True)
class Summary:
    one_sentence_summary: str
    core_ideas: list[str]
    knowledge_points: list[str]
    technical_terms: list[str]
    action_items: list[str]
