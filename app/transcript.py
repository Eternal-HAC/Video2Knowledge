"""Transcript provider boundary.

The default provider is Mock. Real subtitle and Whisper providers are explicit
placeholders until external dependencies are introduced.
"""

from __future__ import annotations

import html
import re
import socket
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

from app.errors import ProviderNotImplementedError, TranscriptProviderError
from app.models import TranscriptResult, TranscriptSegment, VideoMetadata


TRANSCRIPT_PROVIDER_ORDER = [
    "official_subtitles",
    "transcript_api",
    "whisper",
]
OFFICIAL_SUBTITLE_PROVIDER_ID = "yt_dlp_official_subtitles"
OFFICIAL_SUBTITLE_LANGUAGE_PRIORITY = ["zh-CN", "zh-Hans", "zh", "en"]
VTT_CUE_SEPARATOR = "-->"


class TranscriptProvider(Protocol):
    """Interface for acquiring transcript segments."""

    name: str

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        """Acquire transcript data for a video."""


class MockTranscriptProvider:
    name = "mock"

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        return acquire_transcript_mock(metadata)


class RealFallbackTranscriptProvider:
    name = "real-fallback"

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        raise ProviderNotImplementedError(
            "Real transcript fallback is not implemented yet. "
            "Future order: official subtitles, transcript API, Whisper."
        )


class YtDlpOfficialSubtitleProvider:
    name = "official-subtitles"

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        if metadata.platform != "youtube":
            raise TranscriptProviderError(
                "Official subtitle provider currently supports YouTube only."
            )
        if not isinstance(metadata.raw_metadata, dict):
            raise TranscriptProviderError(
                "Official subtitle provider requires yt-dlp raw metadata."
            )

        subtitles = metadata.raw_metadata.get("subtitles")
        if not isinstance(subtitles, dict) or not subtitles:
            raise TranscriptProviderError(
                "No official subtitles found in yt-dlp metadata. "
                "Automatic captions are not used in this stage."
            )

        track = select_official_vtt_track(subtitles)
        if track is None:
            raise TranscriptProviderError(
                "Official subtitles were found, but no VTT/WebVTT track is supported."
            )

        url = _string_value(track.get("url"))
        if not url:
            raise TranscriptProviderError("Selected official subtitle VTT track has no URL.")

        vtt_text = fetch_text(url)
        segments = parse_vtt_segments(vtt_text)
        if not segments:
            raise TranscriptProviderError("Selected official subtitle VTT track has no cues.")

        return TranscriptResult(
            segments=segments,
            provider=OFFICIAL_SUBTITLE_PROVIDER_ID,
            attempted_providers=[OFFICIAL_SUBTITLE_PROVIDER_ID],
        )


def get_mock_transcript(metadata: VideoMetadata) -> list[TranscriptSegment]:
    """Return deterministic transcript segments for Mock processing."""

    return [
        TranscriptSegment("00:00:00", "00:00:20", f"这是来自 {metadata.platform} 的 Mock 视频内容。"),
        TranscriptSegment("00:00:20", "00:00:45", "Video2Knowledge 会把视频信息转成结构化 Markdown。"),
        TranscriptSegment("00:00:45", "00:01:10", "当前阶段只验证本地流水线，不调用真实 API。"),
    ]


def acquire_transcript_mock(metadata: VideoMetadata) -> TranscriptResult:
    """Return Mock transcript data while preserving the future fallback order."""

    return TranscriptResult(
        segments=get_mock_transcript(metadata),
        provider="mock_official_subtitles",
        attempted_providers=TRANSCRIPT_PROVIDER_ORDER,
    )


def acquire_transcript_with_provider(
    metadata: VideoMetadata,
    provider_name: str = "mock",
) -> TranscriptResult:
    """Acquire transcript data with an explicit provider name."""

    provider = build_transcript_provider(provider_name)
    return provider.acquire(metadata)


def build_transcript_provider(provider_name: str) -> TranscriptProvider:
    """Create a transcript provider by name."""

    normalized = provider_name.lower()
    if normalized == "mock":
        return MockTranscriptProvider()
    if normalized == "official-subtitles":
        return YtDlpOfficialSubtitleProvider()
    if normalized == "real-fallback":
        return RealFallbackTranscriptProvider()
    raise ValueError(f"Unknown transcript provider: {provider_name}")


def select_official_vtt_track(
    subtitles: dict[str, object],
) -> dict[str, object] | None:
    """Select the best official VTT/WebVTT subtitle track."""

    for language in OFFICIAL_SUBTITLE_LANGUAGE_PRIORITY:
        track = _first_vtt_track(subtitles.get(language))
        if track is not None:
            return track

    for tracks in subtitles.values():
        track = _first_vtt_track(tracks)
        if track is not None:
            return track

    return None


def parse_vtt_segments(content: str) -> list[TranscriptSegment]:
    """Parse the minimum WebVTT subset used by YouTube official subtitles."""

    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines:
        lines[0] = lines[0].lstrip("\ufeff")

    index = 0
    if lines and lines[0].strip().startswith("WEBVTT"):
        index = 1
        while index < len(lines) and lines[index].strip():
            index += 1

    segments: list[TranscriptSegment] = []
    while index < len(lines):
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines):
            break

        line = lines[index].strip()
        if _is_vtt_metadata_block(line):
            index = _skip_block(lines, index + 1)
            continue

        if VTT_CUE_SEPARATOR in line:
            time_line = line
            index += 1
        else:
            index += 1
            if index >= len(lines):
                break
            time_line = lines[index].strip()
            index += 1

        if VTT_CUE_SEPARATOR not in time_line:
            index = _skip_block(lines, index)
            continue

        start, end = _parse_vtt_time_line(time_line)
        text_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index])
            index += 1

        text = clean_vtt_text(" ".join(text_lines))
        if text:
            segments.append(TranscriptSegment(start=start, end=end, text=text))

    return segments


def clean_vtt_text(text: str) -> str:
    """Remove simple markup and normalize subtitle text."""

    without_tags = re.sub(r"<[^>]+>", "", text)
    unescaped = html.unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def fetch_text(url: str) -> str:
    """Fetch subtitle text without writing subtitle files to disk."""

    try:
        with urlopen(url, timeout=30) as response:
            payload = response.read()
            charset = response.headers.get_content_charset() or "utf-8"
    except HTTPError as error:
        raise TranscriptProviderError(
            f"official subtitle VTT fetch failed: HTTP Error {error.code}"
        ) from error
    except URLError as error:
        if isinstance(error.reason, TimeoutError | socket.timeout):
            raise TranscriptProviderError(
                "official subtitle VTT fetch failed: request timed out"
            ) from error
        raise TranscriptProviderError(
            "official subtitle VTT fetch failed: network request failed"
        ) from error
    except TimeoutError as error:
        raise TranscriptProviderError(
            "official subtitle VTT fetch failed: request timed out"
        ) from error
    except Exception as error:
        raise TranscriptProviderError(
            "official subtitle VTT fetch failed: request failed"
        ) from error
    return payload.decode(charset, errors="replace")


def _first_vtt_track(tracks: object) -> dict[str, object] | None:
    if not isinstance(tracks, list):
        return None
    for track in tracks:
        if isinstance(track, dict) and _is_vtt_track(track):
            return track
    return None


def _is_vtt_track(track: dict[str, object]) -> bool:
    ext = _string_value(track.get("ext")).lower()
    url = _string_value(track.get("url")).lower()
    protocol = _string_value(track.get("protocol")).lower()
    format_note = _string_value(track.get("format")).lower()
    return (
        ext == "vtt"
        or ".vtt" in url
        or "webvtt" in protocol
        or "webvtt" in format_note
    )


def _is_vtt_metadata_block(line: str) -> bool:
    return line.startswith("NOTE") or line in {"STYLE", "REGION"}


def _skip_block(lines: list[str], index: int) -> int:
    while index < len(lines) and lines[index].strip():
        index += 1
    return index


def _parse_vtt_time_line(line: str) -> tuple[str, str]:
    start, remainder = line.split(VTT_CUE_SEPARATOR, 1)
    end = remainder.strip().split()[0]
    return start.strip(), end.strip()


def _string_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)
