"""Regression tests for Markdown artifact reliability hardening.

Covers safe YAML Frontmatter serialization, cwd-independent template
resolution through package resources, and non-overwriting export semantics.
All tests are fully offline; PyYAML is used only when it is already
installed, to prove standard-parser readability without adding a dependency.
"""

from __future__ import annotations

import os
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from app.downloader import get_mock_metadata
from app.exporter.obsidian import export_markdown
from app.markdown_writer import render_markdown
from app.models import Summary, TranscriptSegment
from app.summarizer import summarize_mock
from app.transcript import get_mock_transcript

try:
    import yaml
except ImportError:  # pragma: no cover - environment without PyYAML
    yaml = None

_REQUIRES_YAML = unittest.skipIf(yaml is None, "PyYAML is not installed")


def _metadata_with(**overrides):
    base = get_mock_metadata("https://example.com/watch?v=mock")
    return type(base)(**{**base.__dict__, **overrides})


def _render(**overrides) -> str:
    metadata = _metadata_with(**overrides)
    transcript = get_mock_transcript(metadata)
    summary = summarize_mock(metadata, transcript)
    return render_markdown(metadata, transcript, summary)


def _frontmatter_lines(markdown: str) -> list[str]:
    lines = markdown.splitlines()
    assert lines[0] == "---", "markdown must start with a frontmatter block"
    end = lines.index("---", 1)
    return lines[1:end]


def _frontmatter_text(markdown: str) -> str:
    return "\n".join(_frontmatter_lines(markdown))


def _frontmatter_value(markdown: str, key: str) -> str:
    prefix = f"{key}:"
    for line in _frontmatter_lines(markdown):
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    raise AssertionError(f"frontmatter key {key!r} missing")


class FrontmatterSerializationTests(unittest.TestCase):
    @_REQUIRES_YAML
    def test_normal_frontmatter_round_trips_through_standard_yaml_parser(self) -> None:
        markdown = _render()

        parsed = yaml.safe_load(_frontmatter_text(markdown))

        self.assertEqual(parsed["title"], "Mock Video Knowledge Note")
        self.assertEqual(parsed["platform"], "example.com")
        self.assertEqual(parsed["source_url"], "https://example.com/watch?v=mock")
        self.assertIsInstance(parsed["tags"], list)
        self.assertEqual(parsed["description"], _metadata_with().description)

    @_REQUIRES_YAML
    def test_colons_hashes_and_single_double_quotes_round_trip(self) -> None:
        title = "Colon: value #hash 'single' \"double\""
        author = 'Author: "quoted" #tag'
        markdown = _render(title=title, author=author)

        parsed = yaml.safe_load(_frontmatter_text(markdown))

        self.assertEqual(parsed["title"], title)
        self.assertEqual(parsed["author"], author)

    @_REQUIRES_YAML
    def test_newlines_and_unicode_round_trip(self) -> None:
        title = "第一行\n第二行 \"quoted\" \\ path"
        markdown = _render(title=title, language="中文")

        parsed = yaml.safe_load(_frontmatter_text(markdown))

        self.assertEqual(parsed["title"], title)
        self.assertEqual(parsed["language"], "中文")

    @_REQUIRES_YAML
    def test_yaml_special_looking_strings_keep_string_type(self) -> None:
        markdown = _render(
            title="true",
            author="null",
            published_at="2024-01-02",
            duration="12345",
            status="~",
        )

        parsed = yaml.safe_load(_frontmatter_text(markdown))

        for key, expected in [
            ("title", "true"),
            ("author", "null"),
            ("published_at", "2024-01-02"),
            ("duration", "12345"),
            ("status", "~"),
        ]:
            self.assertEqual(parsed[key], expected)
            self.assertIsInstance(parsed[key], str)

    def test_yaml_special_looking_strings_are_emitted_quoted(self) -> None:
        markdown = _render(title="true", author="null")

        self.assertEqual(_frontmatter_value(markdown, "title"), '"true"')
        self.assertEqual(_frontmatter_value(markdown, "author"), '"null"')

    @_REQUIRES_YAML
    def test_tag_list_elements_are_safely_serialized(self) -> None:
        tags = ["a: b", 'x "y"', "#hash", "true", "中文", "back\\slash"]
        markdown = _render(tags=tags)

        parsed = yaml.safe_load(_frontmatter_text(markdown))

        self.assertEqual(parsed["tags"], tags)

    def test_empty_tag_list_renders_as_empty_flow_sequence(self) -> None:
        markdown = _render(tags=[])

        self.assertEqual(_frontmatter_value(markdown, "tags"), "[]")

    @_REQUIRES_YAML
    def test_empty_and_none_values_are_explicit(self) -> None:
        markdown = _render(author="", language=None, channel_id="")

        parsed = yaml.safe_load(_frontmatter_text(markdown))

        self.assertEqual(parsed["author"], "")
        self.assertIsNone(parsed["language"])

    def test_empty_string_is_emitted_quoted_and_none_as_null(self) -> None:
        markdown = _render(author="", language=None)

        self.assertEqual(_frontmatter_value(markdown, "author"), '""')
        self.assertEqual(_frontmatter_value(markdown, "language"), "null")

    def test_raw_metadata_never_reaches_markdown(self) -> None:
        markdown = _render(
            raw_metadata={"debug_secret": "raw metadata should stay out"},
        )

        self.assertNotIn("raw_metadata", markdown)
        self.assertNotIn("debug_secret", markdown)
        self.assertNotIn("raw metadata should stay out", markdown)

    def test_description_round_trips_with_leading_space_and_raw_metadata_stays_out(self) -> None:
        description = '  Line one: has a colon\nLine two has "double quotes"'
        markdown = _render(
            description=description,
            raw_metadata={"debug_secret": "raw metadata should stay out"},
        )

        parsed = yaml.safe_load(_frontmatter_text(markdown))

        self.assertEqual(parsed["description"], description)
        self.assertNotIn("raw_metadata", markdown)

    @_REQUIRES_YAML
    def test_placeholder_like_metadata_is_not_reinterpreted(self) -> None:
        values = {
            "title": "{{ author_yaml }}",
            "platform": "{{ source_url_yaml }}",
            "source_url": "{{ tags }}",
            "canonical_url": "{{ description_yaml }}",
            "source_id": "{{ status_yaml }}",
            "author": "{{ title_yaml }}",
            "channel_id": "{{ language_yaml }}",
            "published_at": "{{ duration_yaml }}",
            "duration": "{{ platform_yaml }}",
            "language": "{{ thumbnail_url_yaml }}",
            "thumbnail_url": "{{ source_id_yaml }}",
            "status": "{{ canonical_url_yaml }}",
            "description": "{{ one_sentence_summary }}",
        }

        markdown = _render(**values)
        parsed = yaml.safe_load(_frontmatter_text(markdown))

        for key, expected in values.items():
            self.assertEqual(parsed[key], expected)
        self.assertIn("# {{ author_yaml }}", markdown)

    @_REQUIRES_YAML
    def test_control_and_separator_characters_round_trip(self) -> None:
        value = "controls:\x00\x1b\x7f\x80\x81\x85\x9f\u2028\u2029:end"
        markdown = _render(title=value, description=value, tags=[value])

        parsed = yaml.safe_load(_frontmatter_text(markdown))

        self.assertEqual(parsed["title"], value)
        self.assertEqual(parsed["description"], value)
        self.assertEqual(parsed["tags"], [value])

    @_REQUIRES_YAML
    def test_non_bmp_and_lone_surrogate_round_trip(self) -> None:
        title = "emoji:\U0001f642"
        surrogate_value = "surrogate:\ud800"
        markdown = _render(title=title, description=surrogate_value)

        parsed = yaml.safe_load(_frontmatter_text(markdown))

        self.assertEqual(parsed["title"], title)
        self.assertEqual(parsed["description"], surrogate_value)
        markdown.encode("utf-8")

    def test_generated_content_placeholders_are_not_reinterpreted(self) -> None:
        metadata = _metadata_with()
        transcript = [
            TranscriptSegment("00:00:00.000", "00:00:01.000", "{{ title_yaml }}")
        ]
        summary = Summary(
            one_sentence_summary="{{ author_yaml }}",
            core_ideas=["{{ tags }}"],
            knowledge_points=["{{ description_yaml }}"],
            technical_terms=["{{ status_yaml }}"],
            action_items=["{{ source_url_yaml }}"],
        )

        markdown = render_markdown(metadata, transcript, summary)

        for placeholder in [
            "{{ author_yaml }}",
            "{{ tags }}",
            "{{ description_yaml }}",
            "{{ status_yaml }}",
            "{{ source_url_yaml }}",
            "{{ title_yaml }}",
        ]:
            self.assertIn(placeholder, markdown)


class TemplateResolutionTests(unittest.TestCase):
    def test_default_template_loads_from_a_foreign_working_directory(self) -> None:
        original_cwd = Path.cwd()
        with tempfile.TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            try:
                markdown = _render()
            finally:
                os.chdir(original_cwd)

        self.assertIn("## 一句话摘要", markdown)
        self.assertIn("Mock Video Knowledge Note", markdown)

    def test_default_template_is_an_importable_package_resource(self) -> None:
        from importlib import resources

        resource = resources.files("app.templates").joinpath("video_note.md.j2")

        self.assertTrue(resource.is_file())
        content = resource.read_text(encoding="utf-8")
        self.assertIn("{{ title_yaml }}", content)
        self.assertIn("{{ description_yaml }}", content)
        self.assertIn("{{ title }}", content)

    def test_explicit_template_path_is_used_verbatim(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            template_path = Path(temp_dir) / "custom.j2"
            template_path.write_text(
                "TITLE={{ title_yaml }}\nBODY={{ title }}\n", encoding="utf-8"
            )

            markdown = _render_custom(template_path)

        self.assertIn('TITLE="Mock Video Knowledge Note"', markdown)
        self.assertIn("BODY=Mock Video Knowledge Note", markdown)

    def test_missing_explicit_template_fails_without_fallback(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing = Path(temp_dir) / "missing.j2"
            metadata = _metadata_with()
            transcript = get_mock_transcript(metadata)
            summary = summarize_mock(metadata, transcript)

            with self.assertRaises(FileNotFoundError):
                render_markdown(metadata, transcript, summary, missing)

            self.assertFalse(missing.exists())

    def test_packaged_template_matches_repo_template(self) -> None:
        from importlib import resources

        repo_root = Path(__file__).resolve().parent.parent
        repo_template = (repo_root / "templates" / "video_note.md.j2").read_text(
            encoding="utf-8"
        )
        packaged = (
            resources.files("app.templates")
            .joinpath("video_note.md.j2")
            .read_text(encoding="utf-8")
        )

        self.assertEqual(repo_template, packaged)


def _render_custom(template_path: Path) -> str:
    metadata = _metadata_with()
    transcript = get_mock_transcript(metadata)
    summary = summarize_mock(metadata, transcript)
    return render_markdown(metadata, transcript, summary, template_path)


class ExportCollisionTests(unittest.TestCase):
    def test_first_export_uses_base_filename(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = export_markdown("content-one", "Mock Video", temp_dir)

            self.assertEqual(path.name, "mock-video.md")
            self.assertEqual(path.read_text(encoding="utf-8"), "content-one")

    def test_repeated_exports_increment_suffix_instead_of_overwriting(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            first = export_markdown("one", "Mock Video", temp_dir)
            second = export_markdown("two", "Mock Video", temp_dir)
            third = export_markdown("three", "Mock Video", temp_dir)

            self.assertEqual(first.name, "mock-video.md")
            self.assertEqual(second.name, "mock-video-2.md")
            self.assertEqual(third.name, "mock-video-3.md")

    def test_existing_export_is_never_modified(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            original = export_markdown("original", "Mock Video", temp_dir)
            original.write_text("precious", encoding="utf-8")

            export_markdown("replacement", "Mock Video", temp_dir)

            self.assertEqual(original.read_text(encoding="utf-8"), "precious")

    def test_export_returns_the_actually_written_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            (Path(temp_dir) / "mock-video.md").write_text("taken", encoding="utf-8")

            returned = export_markdown("new", "Mock Video", temp_dir)

            self.assertEqual(returned.name, "mock-video-2.md")
            self.assertTrue(returned.exists())
            self.assertEqual(returned.read_text(encoding="utf-8"), "new")

    def test_export_failure_raises_and_leaves_nothing_behind(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch(
                "app.exporter.obsidian.os.open",
                side_effect=OSError("simulated failure"),
            ):
                with self.assertRaises(OSError):
                    export_markdown("payload", "Mock Video", temp_dir)

            self.assertEqual(list(Path(temp_dir).iterdir()), [])

    def test_partial_write_failure_is_cleaned_up_and_raises(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            real_fdopen = os.fdopen

            class FailingHandle:
                def __init__(self, fd):
                    self._handle = real_fdopen(fd, "w", encoding="utf-8")

                def __enter__(self):
                    return self

                def __exit__(self, exc_type, exc_value, traceback):
                    self._handle.close()

                def write(self, content):
                    self._handle.write(content[:3])
                    self._handle.flush()
                    raise OSError("disk full")

            def _failing_fdopen(fd, *args, **kwargs):
                return FailingHandle(fd)

            with mock.patch(
                "app.exporter.obsidian.os.fdopen",
                side_effect=_failing_fdopen,
            ):
                with self.assertRaises(OSError):
                    export_markdown("payload", "Mock Video", temp_dir)

            self.assertEqual(list(Path(temp_dir).iterdir()), [])

    def test_concurrent_exports_never_overwrite_each_other(self) -> None:
        thread_count = 8
        barrier = threading.Barrier(thread_count)
        returned: list[Path] = []
        errors: list[BaseException] = []

        def _export() -> None:
            try:
                barrier.wait(timeout=30)
                path = export_markdown("unique-payload", "Mock Video", temp_dir)
            except BaseException as error:  # noqa: BLE001 - test collector
                errors.append(error)
            else:
                returned.append(path)

        with tempfile.TemporaryDirectory() as temp_dir:
            workers = [
                threading.Thread(target=_export) for _ in range(thread_count)
            ]
            for worker in workers:
                worker.start()
            for worker in workers:
                worker.join(timeout=30)

            self.assertEqual(errors, [])
            self.assertEqual(len(returned), thread_count)
            self.assertEqual(
                len({path.name for path in returned}), thread_count
            )
            for path in returned:
                self.assertEqual(path.read_text(encoding="utf-8"), "unique-payload")

    def test_unicode_title_exports_on_windows(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = export_markdown("unicode", "中文 标题 Video", temp_dir)

            self.assertTrue(path.exists())
            self.assertEqual(path.suffix, ".md")
            self.assertIn("中文", path.name)

    def test_windows_forbidden_characters_do_not_break_export(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = export_markdown("content", 'forbidden <>:/\\|?*" chars', temp_dir)

            self.assertTrue(path.exists())
            self.assertNotIn("<", path.name)
            self.assertNotIn(":", path.name)


if __name__ == "__main__":
    unittest.main()
