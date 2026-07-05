"""Mock transcript provider.

This module does not fetch official subtitles or external transcripts in Stage 1.
"""

from __future__ import annotations

from app.models import TranscriptSegment, VideoMetadata


def get_mock_transcript(metadata: VideoMetadata) -> list[TranscriptSegment]:
    """Return deterministic transcript segments for Mock processing."""

    return [
        TranscriptSegment("00:00:00", "00:00:20", f"这是来自 {metadata.platform} 的 Mock 视频内容。"),
        TranscriptSegment("00:00:20", "00:00:45", "Video2Knowledge 会把视频信息转成结构化 Markdown。"),
        TranscriptSegment("00:00:45", "00:01:10", "第一阶段只验证本地流水线，不调用真实 API。"),
    ]

