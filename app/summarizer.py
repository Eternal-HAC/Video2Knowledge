"""Mock summarizer.

This module does not call an LLM in Stage 1.
"""

from __future__ import annotations

from app.models import Summary, TranscriptSegment, VideoMetadata


def summarize_mock(metadata: VideoMetadata, transcript: list[TranscriptSegment]) -> Summary:
    """Return deterministic knowledge extraction output."""

    _ = transcript
    return Summary(
        one_sentence_summary=(
            f"{metadata.title} 演示了 Video2Knowledge 的本地 Mock 知识处理闭环。"
        ),
        core_ideas=[
            "先建立可运行的端到端流程，再替换真实能力。",
            "项目价值集中在知识抽取和结构化输出，而不是重复造媒体处理轮子。",
            "Local First 让知识资产优先保存在本地。",
        ],
        knowledge_points=[
            "Mock MVP 用于验证模块边界和 Markdown 输出契约。",
            "真实下载、字幕、Whisper 和 LLM 都将在后续阶段接入。",
            "YAML Frontmatter 让 Obsidian Dataview、Git 和检索更容易协作。",
        ],
        technical_terms=[
            "Local First",
            "YAML Frontmatter",
            "Mock Pipeline",
            "Personal Knowledge Management",
        ],
        action_items=[
            "确认 Mock Markdown 输出格式是否满足 Obsidian 使用习惯。",
            "下一阶段接入平台适配器和字幕获取策略。",
        ],
    )

