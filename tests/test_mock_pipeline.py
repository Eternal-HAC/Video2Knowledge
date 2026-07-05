from __future__ import annotations

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from app.cli import main, run_import_url
from app.downloader import get_mock_metadata, get_metadata_with_provider
from app.errors import ProviderNotImplementedError
from app.markdown_writer import render_markdown
from app.platform_adapter import resolve_video_source
from app.summarizer import summarize_mock
from app.transcript import (
    acquire_transcript_mock,
    acquire_transcript_with_provider,
    get_mock_transcript,
)


class MockPipelineTests(unittest.TestCase):
    def test_mock_metadata_keeps_source_url(self) -> None:
        url = "https://example.com/watch?v=mock"

        metadata = get_mock_metadata(url)

        self.assertEqual(metadata.source_url, url)
        self.assertEqual(metadata.status, "mock")
        self.assertIn("mock", metadata.tags)

    def test_platform_adapter_detects_youtube_url(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=mock")

        self.assertEqual(source.source_type, "url")
        self.assertEqual(source.platform, "youtube")

        metadata = get_metadata_with_provider(source)

        self.assertEqual(metadata.platform, "youtube")

    def test_transcript_result_records_mock_strategy(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")

        result = acquire_transcript_mock(metadata)

        self.assertEqual(result.provider, "mock_official_subtitles")
        self.assertEqual(
            result.attempted_providers,
            ["official_subtitles", "transcript_api", "whisper"],
        )
        self.assertTrue(result.segments)

    def test_real_metadata_provider_boundary_is_explicitly_unimplemented(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=mock")

        with self.assertRaises(ProviderNotImplementedError):
            get_metadata_with_provider(source, provider_name="yt-dlp")

    def test_real_transcript_provider_boundary_is_explicitly_unimplemented(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")

        with self.assertRaises(ProviderNotImplementedError):
            acquire_transcript_with_provider(metadata, provider_name="real-fallback")

    def test_render_markdown_contains_required_frontmatter_and_sections(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")
        transcript = get_mock_transcript(metadata)
        summary = summarize_mock(metadata, transcript)

        markdown = render_markdown(metadata, transcript, summary)

        for field in [
            "title:",
            "platform:",
            "source_url:",
            "author:",
            "published_at:",
            "imported_at:",
            "duration:",
            "language:",
            "tags:",
            "status:",
        ]:
            self.assertIn(field, markdown)

        for section in [
            "## 一句话摘要",
            "## 核心观点",
            "## 知识点",
            "## 技术术语",
            "## 可执行事项",
            "## 原始转录（带时间戳）",
        ]:
            self.assertIn(section, markdown)

    def test_run_import_url_writes_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = run_import_url("https://example.com/watch?v=mock", temp_dir)

            self.assertTrue(path.exists())
            self.assertEqual(path.suffix, ".md")
            self.assertIn("Mock Video Knowledge Note", path.read_text(encoding="utf-8"))

    def test_cli_import_url_returns_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code = main(
                [
                    "import-url",
                    "https://example.com/watch?v=mock",
                    "--output-dir",
                    temp_dir,
                ]
            )

            self.assertEqual(exit_code, 0)
            self.assertTrue(list(Path(temp_dir).glob("*.md")))

    def test_cli_non_mock_provider_returns_clear_error(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as temp_dir:
            with contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "import-url",
                        "https://example.com/watch?v=mock",
                        "--metadata-provider",
                        "yt-dlp",
                        "--output-dir",
                        temp_dir,
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertIn("yt-dlp metadata provider is not implemented yet", stderr.getvalue())


if __name__ == "__main__":
    unittest.main()
