from __future__ import annotations

import contextlib
import io
import socket
import sys
import tempfile
import types
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest import mock

from app.cli import main, run_import_url
from app.downloader import get_mock_metadata, get_metadata_with_provider
from app.errors import (
    MetadataProviderError,
    NetworkAccessError,
    NoOfficialSubtitleError,
    PlatformAccessError,
    ProviderNotImplementedError,
    TranscriptProviderError,
    UnsupportedSubtitleFormatError,
)
from app.markdown_writer import render_markdown
from app.pipeline import ImportPipelineOptions, run_import_pipeline
from app.platform_adapter import get_platform_capabilities, resolve_video_source
from app.summarizer import summarize_mock
from app.transcript import (
    OFFICIAL_SUBTITLE_PROVIDER_ID,
    acquire_transcript_mock,
    acquire_transcript_with_provider,
    fetch_text,
    get_mock_transcript,
    parse_vtt_segments,
    select_official_vtt_track,
    should_fallback_to_whisper,
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
        self.assertEqual(metadata.source_id, "mock")
        self.assertEqual(metadata.canonical_url, "https://www.youtube.com/watch?v=mock")

    def test_platform_capabilities_describe_youtube_and_local(self) -> None:
        youtube = get_platform_capabilities("youtube")
        local = get_platform_capabilities("local")
        unknown = get_platform_capabilities("unknown")

        self.assertTrue(youtube.supports_metadata)
        self.assertTrue(youtube.supports_transcript)
        self.assertTrue(youtube.supports_cookies)
        self.assertIn("yt-dlp", youtube.metadata_providers)
        self.assertIn("official-subtitles", youtube.transcript_providers)
        self.assertTrue(local.supports_local_file)
        self.assertFalse(local.supports_cookies)
        self.assertFalse(unknown.supports_metadata)

    def test_transcript_result_records_mock_strategy(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")

        result = acquire_transcript_mock(metadata)

        self.assertEqual(result.provider, "mock_official_subtitles")
        self.assertEqual(
            result.attempted_providers,
            ["official_subtitles", "transcript_api", "whisper"],
        )
        self.assertTrue(result.segments)

    def test_ytdlp_provider_does_not_affect_mock_flow_when_uninstalled(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=mock")

        with mock.patch.dict(sys.modules, {"yt_dlp": None}):
            with self.assertRaises(MetadataProviderError):
                get_metadata_with_provider(source, provider_name="yt-dlp")

    def test_ytdlp_metadata_provider_maps_sanitized_info(self) -> None:
        url = "https://www.youtube.com/watch?v=real123"
        source = resolve_video_source(url)
        raw_info = {
            "id": "real123",
            "title": "Real Metadata Title",
            "uploader": "Example Uploader",
            "channel_id": "UC123",
            "description": "Long description",
            "upload_date": "20260705",
            "duration": 3723,
            "thumbnail": "https://example.com/thumb.jpg",
            "webpage_url": "https://www.youtube.com/watch?v=real123",
            "language": "en",
            "tags": ["ai", "metadata"],
            "extra_field": {"nested": True},
        }
        fake_module, fake_ydl_class = _fake_ytdlp_module(raw_info)

        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
            metadata = get_metadata_with_provider(source, provider_name="yt-dlp")

        instance = fake_ydl_class.instances[0]
        self.assertEqual(instance.extract_calls, [(url, False)])
        self.assertEqual(metadata.title, "Real Metadata Title")
        self.assertEqual(metadata.platform, "youtube")
        self.assertEqual(metadata.source_id, "real123")
        self.assertEqual(metadata.canonical_url, "https://www.youtube.com/watch?v=real123")
        self.assertEqual(metadata.author, "Example Uploader")
        self.assertEqual(metadata.channel_id, "UC123")
        self.assertEqual(metadata.description, "Long description")
        self.assertEqual(metadata.published_at, "2026-07-05")
        self.assertEqual(metadata.duration, "01:02:03")
        self.assertEqual(metadata.thumbnail_url, "https://example.com/thumb.jpg")
        self.assertEqual(metadata.status, "metadata_only")
        self.assertIn("youtube", metadata.tags)
        self.assertEqual(metadata.raw_metadata, raw_info)

    def test_ytdlp_metadata_provider_rejects_non_youtube_source(self) -> None:
        source = resolve_video_source("https://example.com/watch?v=real123")

        with self.assertRaises(MetadataProviderError):
            get_metadata_with_provider(source, provider_name="yt-dlp")

    def test_ytdlp_metadata_provider_reports_missing_dependency(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=real123")

        with mock.patch.dict(sys.modules, {"yt_dlp": None}):
            with self.assertRaises(MetadataProviderError):
                get_metadata_with_provider(source, provider_name="yt-dlp")

    def test_real_fallback_preserves_non_youtube_platform_error(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")

        with self.assertRaises(PlatformAccessError):
            acquire_transcript_with_provider(metadata, provider_name="real-fallback")

    def test_official_subtitle_provider_selects_priority_vtt_track(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {
                "subtitles": {
                    "en": [{"ext": "vtt", "url": "https://example.com/en.vtt"}],
                    "zh-CN": [{"ext": "vtt", "url": "https://example.com/zh.vtt"}],
                }
            }
        )
        vtt = """WEBVTT

1
00:00:01.000 --> 00:00:03.000
Hello &amp; welcome
"""

        with mock.patch("app.transcript.fetch_text", return_value=vtt) as fetch_text:
            result = acquire_transcript_with_provider(
                metadata,
                provider_name="official-subtitles",
            )

        fetch_text.assert_called_once_with("https://example.com/zh.vtt")
        self.assertEqual(result.provider, OFFICIAL_SUBTITLE_PROVIDER_ID)
        self.assertEqual(result.attempted_providers, [OFFICIAL_SUBTITLE_PROVIDER_ID])
        self.assertEqual(result.segments[0].start, "00:00:01.000")
        self.assertEqual(result.segments[0].end, "00:00:03.000")
        self.assertEqual(result.segments[0].text, "Hello & welcome")

    def test_official_subtitle_provider_ignores_automatic_captions(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {
                "automatic_captions": {
                    "en": [{"ext": "vtt", "url": "https://example.com/auto.vtt"}],
                }
            }
        )

        with self.assertRaises(NoOfficialSubtitleError) as context:
            acquire_transcript_with_provider(metadata, provider_name="official-subtitles")
        self.assertTrue(should_fallback_to_whisper(context.exception))

    def test_official_subtitle_provider_rejects_non_vtt_official_tracks(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {
                "subtitles": {
                    "en": [{"ext": "json3", "url": "https://example.com/en.json3"}],
                }
            }
        )

        with self.assertRaises(UnsupportedSubtitleFormatError) as context:
            acquire_transcript_with_provider(metadata, provider_name="official-subtitles")
        self.assertTrue(should_fallback_to_whisper(context.exception))

    def test_official_subtitle_provider_rejects_non_youtube_metadata(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")

        with self.assertRaises(PlatformAccessError) as context:
            acquire_transcript_with_provider(metadata, provider_name="official-subtitles")
        self.assertFalse(should_fallback_to_whisper(context.exception))

    def test_official_subtitle_provider_missing_subtitles_is_fallback_eligible(self) -> None:
        metadata = _youtube_metadata_with_raw({})

        with self.assertRaises(NoOfficialSubtitleError) as context:
            acquire_transcript_with_provider(metadata, provider_name="official-subtitles")

        self.assertTrue(should_fallback_to_whisper(context.exception))

    def test_official_subtitle_provider_empty_subtitles_is_fallback_eligible(self) -> None:
        metadata = _youtube_metadata_with_raw({"subtitles": {}})

        with self.assertRaises(NoOfficialSubtitleError) as context:
            acquire_transcript_with_provider(metadata, provider_name="official-subtitles")

        self.assertTrue(should_fallback_to_whisper(context.exception))

    def test_official_subtitle_provider_raw_metadata_contract_error_is_not_fallback(self) -> None:
        metadata = get_mock_metadata("https://www.youtube.com/watch?v=mock", platform="youtube")
        metadata = type(metadata)(**{**metadata.__dict__, "raw_metadata": None})

        with self.assertRaises(TranscriptProviderError) as context:
            acquire_transcript_with_provider(metadata, provider_name="official-subtitles")

        self.assertNotIsInstance(context.exception, NoOfficialSubtitleError)
        self.assertFalse(should_fallback_to_whisper(context.exception))

    def test_select_official_vtt_track_falls_back_to_first_supported_language(self) -> None:
        track = select_official_vtt_track(
            {
                "fr": [{"ext": "json3", "url": "https://example.com/fr.json3"}],
                "de": [{"url": "https://example.com/de.vtt"}],
            }
        )

        self.assertEqual(track, {"url": "https://example.com/de.vtt"})

    def test_parse_vtt_segments_supports_minimum_webvtt_subset(self) -> None:
        vtt = """WEBVTT
Kind: captions

NOTE this block should be skipped
temporary note

STYLE
::cue { color: white }

REGION
id:fred

1
00:00:01.000 --> 00:00:03.500 align:start position:0%
<v Speaker>Line one &amp; two
continues here

2
00:00:04.000 --> 00:00:06.000
Text with <b>bold</b> and&nbsp;entity
"""

        segments = parse_vtt_segments(vtt)

        self.assertEqual(len(segments), 2)
        self.assertEqual(segments[0].start, "00:00:01.000")
        self.assertEqual(segments[0].end, "00:00:03.500")
        self.assertEqual(segments[0].text, "Line one & two continues here")
        self.assertEqual(segments[1].start, "00:00:04.000")
        self.assertEqual(segments[1].end, "00:00:06.000")
        self.assertEqual(segments[1].text, "Text with bold and entity")

    def test_fetch_text_wraps_http_429_without_sensitive_url(self) -> None:
        sensitive_url = "https://example.com/sub.vtt?signature=secret&token=hidden"
        error = HTTPError(sensitive_url, 429, "Too Many Requests", hdrs=None, fp=None)

        with mock.patch("app.transcript.urlopen", side_effect=error):
            with self.assertRaises(PlatformAccessError) as context:
                fetch_text(sensitive_url)

        message = str(context.exception)
        self.assertEqual(
            message,
            "official subtitle VTT fetch failed: HTTP Error 429",
        )
        _assert_sensitive_subtitle_url_not_leaked(self, message)
        self.assertFalse(should_fallback_to_whisper(context.exception))

    def test_fetch_text_wraps_http_403(self) -> None:
        error = HTTPError("https://example.com/sub.vtt", 403, "Forbidden", hdrs=None, fp=None)

        with mock.patch("app.transcript.urlopen", side_effect=error):
            with self.assertRaises(PlatformAccessError) as context:
                fetch_text("https://example.com/sub.vtt")

        self.assertEqual(
            str(context.exception),
            "official subtitle VTT fetch failed: HTTP Error 403",
        )
        self.assertFalse(should_fallback_to_whisper(context.exception))

    def test_fetch_text_wraps_url_error_without_raw_reason(self) -> None:
        sensitive_url = "https://example.com/sub.vtt?signature=secret&token=hidden"

        with mock.patch("app.transcript.urlopen", side_effect=URLError(sensitive_url)):
            with self.assertRaises(NetworkAccessError) as context:
                fetch_text(sensitive_url)

        message = str(context.exception)
        self.assertEqual(
            message,
            "official subtitle VTT fetch failed: network request failed",
        )
        _assert_sensitive_subtitle_url_not_leaked(self, message)
        self.assertFalse(should_fallback_to_whisper(context.exception))

    def test_fetch_text_maps_url_error_socket_timeout_to_timeout(self) -> None:
        sensitive_url = "https://example.com/sub.vtt?signature=secret&token=hidden"

        with mock.patch(
            "app.transcript.urlopen",
            side_effect=URLError(socket.timeout("timed out with secret")),
        ):
            with self.assertRaises(NetworkAccessError) as context:
                fetch_text(sensitive_url)

        message = str(context.exception)
        self.assertEqual(
            message,
            "official subtitle VTT fetch failed: request timed out",
        )
        _assert_sensitive_subtitle_url_not_leaked(self, message)
        self.assertNotIn("timed out with secret", message)
        self.assertFalse(should_fallback_to_whisper(context.exception))

    def test_fetch_text_wraps_timeout(self) -> None:
        with mock.patch("app.transcript.urlopen", side_effect=TimeoutError()):
            with self.assertRaises(NetworkAccessError) as context:
                fetch_text("https://example.com/sub.vtt")

        self.assertEqual(
            str(context.exception),
            "official subtitle VTT fetch failed: request timed out",
        )
        self.assertFalse(should_fallback_to_whisper(context.exception))

    def test_fetch_text_wraps_unknown_request_failure(self) -> None:
        with mock.patch("app.transcript.urlopen", side_effect=RuntimeError("secret failure")):
            with self.assertRaises(NetworkAccessError) as context:
                fetch_text("https://example.com/sub.vtt")

        self.assertEqual(
            str(context.exception),
            "official subtitle VTT fetch failed: request failed",
        )
        self.assertNotIn("secret failure", str(context.exception))
        self.assertFalse(should_fallback_to_whisper(context.exception))

    def test_official_subtitle_no_cues_is_not_fallback_eligible(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {"subtitles": {"zh-CN": [{"ext": "vtt", "url": "https://example.com/zh.vtt"}]}}
        )

        with mock.patch("app.transcript.fetch_text", return_value="WEBVTT\n\n"):
            with self.assertRaises(TranscriptProviderError) as context:
                acquire_transcript_with_provider(metadata, provider_name="official-subtitles")

        self.assertFalse(should_fallback_to_whisper(context.exception))

    def test_real_fallback_reports_eligible_no_subtitles_without_running_whisper(self) -> None:
        metadata = _youtube_metadata_with_raw({})

        with self.assertRaises(ProviderNotImplementedError) as context:
            acquire_transcript_with_provider(metadata, provider_name="real-fallback")

        self.assertIn(
            "Whisper fallback is eligible but not implemented in this stage: "
            "no official subtitles found.",
            str(context.exception),
        )

    def test_real_fallback_reports_eligible_unsupported_subtitle_format(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {"subtitles": {"en": [{"ext": "json3", "url": "https://example.com/en.json3"}]}}
        )

        with self.assertRaises(ProviderNotImplementedError) as context:
            acquire_transcript_with_provider(metadata, provider_name="real-fallback")

        self.assertIn(
            "Whisper fallback is eligible but not implemented in this stage: "
            "official subtitles have no VTT/WebVTT track.",
            str(context.exception),
        )

    def test_real_fallback_preserves_platform_access_error(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {"subtitles": {"zh-CN": [{"ext": "vtt", "url": "https://example.com/zh.vtt"}]}}
        )
        error = HTTPError("https://example.com/zh.vtt", 429, "Too Many Requests", None, None)

        with mock.patch("app.transcript.urlopen", side_effect=error):
            with self.assertRaises(PlatformAccessError):
                acquire_transcript_with_provider(metadata, provider_name="real-fallback")

    def test_real_fallback_preserves_network_access_error(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {"subtitles": {"zh-CN": [{"ext": "vtt", "url": "https://example.com/zh.vtt"}]}}
        )

        with mock.patch("app.transcript.urlopen", side_effect=URLError("network secret")):
            with self.assertRaises(NetworkAccessError):
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
            "canonical_url:",
            "source_id:",
            "author:",
            "channel_id:",
            "published_at:",
            "imported_at:",
            "duration:",
            "language:",
            "thumbnail_url:",
            "tags:",
            "status:",
            "description:",
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

    def test_render_markdown_does_not_include_raw_metadata(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")
        metadata = type(metadata)(
            **{
                **metadata.__dict__,
                "raw_metadata": {"debug_secret": "raw metadata should stay out"},
            }
        )
        transcript = get_mock_transcript(metadata)
        summary = summarize_mock(metadata, transcript)

        markdown = render_markdown(metadata, transcript, summary)

        self.assertNotIn("raw_metadata", markdown)
        self.assertNotIn("debug_secret", markdown)
        self.assertNotIn("raw metadata should stay out", markdown)

    def test_render_markdown_description_uses_safe_yaml_block(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")
        metadata = type(metadata)(
            **{
                **metadata.__dict__,
                "description": "\n".join(
                    [
                        "Line one: has a colon",
                        'Line two has "double quotes"',
                        "URL: https://example.com/watch?v=mock",
                        "# Heading-looking text",
                        "- Markdown list item",
                    ]
                ),
                "raw_metadata": {"debug_secret": "raw metadata should stay out"},
            }
        )
        transcript = get_mock_transcript(metadata)
        summary = summarize_mock(metadata, transcript)

        markdown = render_markdown(metadata, transcript, summary)

        self.assertIn("description: |-", markdown)
        self.assertIn("  Line one: has a colon", markdown)
        self.assertIn('  Line two has "double quotes"', markdown)
        self.assertIn("  URL: https://example.com/watch?v=mock", markdown)
        self.assertIn("  # Heading-looking text", markdown)
        self.assertIn("  - Markdown list item", markdown)
        self.assertNotIn("raw_metadata", markdown)
        self.assertNotIn("debug_secret", markdown)
        self.assertNotIn("raw metadata should stay out", markdown)

    def test_run_import_url_writes_markdown_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = run_import_url("https://example.com/watch?v=mock", temp_dir)

            self.assertTrue(path.exists())
            self.assertEqual(path.suffix, ".md")
            self.assertIn("Mock Video Knowledge Note", path.read_text(encoding="utf-8"))

    def test_pipeline_runs_complete_mock_flow(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            result = run_import_pipeline(
                "https://www.youtube.com/watch?v=mock",
                ImportPipelineOptions(output_dir=temp_dir),
            )

            self.assertEqual(result.source.platform, "youtube")
            self.assertEqual(result.metadata.source_id, "mock")
            self.assertEqual(result.transcript_result.provider, "mock_official_subtitles")
            self.assertTrue(result.summary.one_sentence_summary)
            self.assertTrue(result.output_path.exists())

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
        self.assertIn("Error:", stderr.getvalue())
        self.assertIn("yt-dlp metadata provider currently supports YouTube only", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_cli_official_subtitle_error_returns_clear_error(self) -> None:
        stderr = io.StringIO()

        with tempfile.TemporaryDirectory() as temp_dir:
            with contextlib.redirect_stderr(stderr):
                exit_code = main(
                    [
                        "import-url",
                        "https://www.youtube.com/watch?v=mock",
                        "--metadata-provider",
                        "mock",
                        "--transcript-provider",
                        "official-subtitles",
                        "--output-dir",
                        temp_dir,
                    ]
                )

        self.assertEqual(exit_code, 1)
        self.assertIn("Error:", stderr.getvalue())
        self.assertIn("No official subtitles found", stderr.getvalue())
        self.assertNotIn("Traceback", stderr.getvalue())

    def test_cli_official_subtitle_fetch_error_is_sanitized(self) -> None:
        stderr = io.StringIO()
        sensitive_url = "https://example.com/sub.vtt?signature=secret&token=hidden"
        raw_metadata = {
            "id": "real123",
            "title": "Real Metadata Title",
            "uploader": "Example Uploader",
            "webpage_url": "https://www.youtube.com/watch?v=real123",
            "subtitles": {
                "zh-CN": [{"ext": "vtt", "url": sensitive_url}],
            },
        }
        fake_module, _ = _fake_ytdlp_module(raw_metadata)
        error = HTTPError(sensitive_url, 429, "Too Many Requests", hdrs=None, fp=None)

        with tempfile.TemporaryDirectory() as temp_dir:
            with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
                with mock.patch("app.transcript.urlopen", side_effect=error):
                    with contextlib.redirect_stderr(stderr):
                        exit_code = main(
                            [
                                "import-url",
                                "https://www.youtube.com/watch?v=real123",
                                "--metadata-provider",
                                "yt-dlp",
                                "--transcript-provider",
                                "official-subtitles",
                                "--output-dir",
                                temp_dir,
                            ]
                        )

        output = stderr.getvalue()
        self.assertEqual(exit_code, 1)
        self.assertIn("Error: official subtitle VTT fetch failed: HTTP Error 429", output)
        self.assertNotIn("Traceback", output)
        _assert_sensitive_subtitle_url_not_leaked(self, output)


def _fake_ytdlp_module(raw_info: dict[str, object]):
    class FakeYoutubeDL:
        instances = []

        def __init__(self, opts):
            self.opts = opts
            self.extract_calls = []
            FakeYoutubeDL.instances.append(self)

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download):
            self.extract_calls.append((url, download))
            return raw_info

        def sanitize_info(self, info):
            return info

    return types.SimpleNamespace(YoutubeDL=FakeYoutubeDL), FakeYoutubeDL


def _youtube_metadata_with_raw(raw_metadata: dict[str, object]):
    metadata = get_mock_metadata(
        "https://www.youtube.com/watch?v=real123",
        platform="youtube",
    )
    return type(metadata)(
        **{
            **metadata.__dict__,
            "status": "metadata_only",
            "source_id": "real123",
            "raw_metadata": raw_metadata,
        }
    )


def _assert_sensitive_subtitle_url_not_leaked(
    test_case: unittest.TestCase,
    output: str,
) -> None:
    for sensitive_value in [
        "https://example.com/sub.vtt",
        "signature",
        "token",
        "secret",
        "hidden",
    ]:
        test_case.assertNotIn(sensitive_value, output)


if __name__ == "__main__":
    unittest.main()
