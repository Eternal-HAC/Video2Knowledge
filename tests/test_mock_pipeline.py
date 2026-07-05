from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from app.cli import main, run_import_url
from app.downloader import get_mock_metadata
from app.markdown_writer import render_markdown
from app.summarizer import summarize_mock
from app.transcript import get_mock_transcript


class MockPipelineTests(unittest.TestCase):
    def test_mock_metadata_keeps_source_url(self) -> None:
        url = "https://example.com/watch?v=mock"

        metadata = get_mock_metadata(url)

        self.assertEqual(metadata.source_url, url)
        self.assertEqual(metadata.status, "mock")
        self.assertIn("mock", metadata.tags)

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


if __name__ == "__main__":
    unittest.main()

