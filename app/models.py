"""Shared data structures for the Mock MVP pipeline."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class VideoSource:
    raw_input: str
    source_type: str
    platform: str


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
