from __future__ import annotations

import contextlib
import io
import socket
import subprocess
import sys
import tempfile
import types
import unittest
from pathlib import Path
from urllib.error import HTTPError, URLError
from unittest import mock

from app.audio import (
    AudioArtifact,
    FfmpegAudioNormalizer,
    LOCAL_FILE_AUDIO_PROVIDER_ID,
    LocalFileAudioProvider,
    MockAudioNormalizer,
    MockAudioProvider,
    NormalizedAudio,
    YT_DLP_AUDIO_PROVIDER_ID,
    YtDlpAudioProvider,
)
from app.cli import main, run_import_url
from app.downloader import get_mock_metadata, get_metadata_with_provider
from app.errors import (
    AudioAcquisitionError,
    AudioProcessingError,
    FfmpegNotFoundError,
    MetadataProviderError,
    NetworkAccessError,
    NoOfficialSubtitleError,
    PlatformAccessError,
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
from app.whisper import LOCAL_WHISPER_MOCK_PROVIDER_ID, MockWhisperBackend


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

    def test_real_fallback_returns_official_subtitles_without_mock_whisper(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {"subtitles": {"zh-CN": [{"ext": "vtt", "url": "https://example.com/zh.vtt"}]}}
        )
        vtt = """WEBVTT

00:00:01.000 --> 00:00:03.000
Official subtitle text
"""

        with mock.patch("app.transcript.fetch_text", return_value=vtt):
            with mock.patch("app.transcript.MockAudioProvider") as audio_provider:
                with mock.patch("app.transcript.MockAudioNormalizer") as normalizer:
                    with mock.patch("app.transcript.MockWhisperBackend") as backend:
                        result = acquire_transcript_with_provider(
                            metadata,
                            provider_name="real-fallback",
                        )

        audio_provider.assert_not_called()
        normalizer.assert_not_called()
        backend.assert_not_called()
        self.assertEqual(result.provider, OFFICIAL_SUBTITLE_PROVIDER_ID)
        self.assertEqual(result.attempted_providers, [OFFICIAL_SUBTITLE_PROVIDER_ID])
        self.assertEqual(result.segments[0].text, "Official subtitle text")

    def test_real_fallback_uses_mock_audio_boundary_for_missing_subtitles(self) -> None:
        metadata = _youtube_metadata_with_raw({})
        audio = AudioArtifact(
            path=Path("mock-audio.wav"),
            provider="mock_audio_provider",
            format="wav",
            temporary=True,
        )
        normalized = NormalizedAudio(
            path=Path("normalized-mock-audio.wav"),
            provider="mock_ffmpeg_normalizer",
            format="wav",
            sample_rate=16000,
            channels=1,
            temporary=True,
        )

        with mock.patch("app.transcript.MockAudioProvider") as audio_provider:
            with mock.patch("app.transcript.MockAudioNormalizer") as normalizer:
                audio_provider.return_value.acquire.return_value = audio
                normalizer.return_value.normalize.return_value = normalized
                result = acquire_transcript_with_provider(
                    metadata,
                    provider_name="real-fallback",
                )

        audio_provider.return_value.acquire.assert_called_once_with(metadata)
        normalizer.return_value.normalize.assert_called_once_with(audio)
        self.assertEqual(result.provider, LOCAL_WHISPER_MOCK_PROVIDER_ID)
        self.assertEqual(
            result.attempted_providers,
            [OFFICIAL_SUBTITLE_PROVIDER_ID, LOCAL_WHISPER_MOCK_PROVIDER_ID],
        )

    def test_real_fallback_uses_mock_whisper_for_missing_subtitles(self) -> None:
        metadata = _youtube_metadata_with_raw({})

        result = acquire_transcript_with_provider(metadata, provider_name="real-fallback")

        self.assertEqual(result.provider, LOCAL_WHISPER_MOCK_PROVIDER_ID)
        self.assertEqual(
            result.attempted_providers,
            [OFFICIAL_SUBTITLE_PROVIDER_ID, LOCAL_WHISPER_MOCK_PROVIDER_ID],
        )
        self.assertEqual(len(result.segments), 3)
        self.assertIn("Mock Whisper fallback transcript", result.segments[0].text)

    def test_real_fallback_uses_mock_whisper_for_unsupported_subtitle_format(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {"subtitles": {"en": [{"ext": "json3", "url": "https://example.com/en.json3"}]}}
        )
        audio = AudioArtifact(
            path=Path("mock-audio.wav"),
            provider="mock_audio_provider",
            format="wav",
            temporary=True,
        )

        with mock.patch("app.transcript.MockAudioProvider") as audio_provider:
            with mock.patch("app.transcript.MockAudioNormalizer") as normalizer:
                audio_provider.return_value.acquire.return_value = audio
                result = acquire_transcript_with_provider(metadata, provider_name="real-fallback")

        audio_provider.return_value.acquire.assert_called_once_with(metadata)
        normalizer.return_value.normalize.assert_called_once_with(audio)
        self.assertEqual(result.provider, LOCAL_WHISPER_MOCK_PROVIDER_ID)
        self.assertEqual(
            result.attempted_providers,
            [OFFICIAL_SUBTITLE_PROVIDER_ID, LOCAL_WHISPER_MOCK_PROVIDER_ID],
        )
        self.assertTrue(result.segments)

    def test_mock_whisper_backend_returns_stable_transcript_result(self) -> None:
        metadata = _youtube_metadata_with_raw({})

        result = MockWhisperBackend().transcribe(metadata)

        self.assertEqual(result.provider, LOCAL_WHISPER_MOCK_PROVIDER_ID)
        self.assertEqual(result.attempted_providers, [LOCAL_WHISPER_MOCK_PROVIDER_ID])
        self.assertEqual(len(result.segments), 3)
        self.assertEqual(result.segments[0].start, "00:00:00")
        self.assertEqual(result.segments[0].end, "00:00:15")
        self.assertIn("Mock Whisper fallback transcript", result.segments[0].text)

    def test_mock_audio_provider_does_not_create_media_file(self) -> None:
        metadata = _youtube_metadata_with_raw({})

        artifact = MockAudioProvider().acquire(metadata)

        self.assertEqual(artifact.provider, "mock_audio_provider")
        self.assertEqual(artifact.format, "wav")
        self.assertTrue(artifact.temporary)
        self.assertFalse(artifact.path.exists())

    def test_local_file_audio_provider_returns_user_owned_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.M4A"
            input_path.write_bytes(b"user-owned audio")
            files_before = list(Path(temp_dir).iterdir())
            metadata = get_mock_metadata(str(input_path), platform="local")

            artifact = LocalFileAudioProvider().acquire(metadata)

            self.assertEqual(artifact.path, input_path)
            self.assertEqual(artifact.provider, LOCAL_FILE_AUDIO_PROVIDER_ID)
            self.assertEqual(artifact.format, "m4a")
            self.assertFalse(artifact.temporary)
            self.assertEqual(input_path.read_bytes(), b"user-owned audio")
            self.assertEqual(list(Path(temp_dir).iterdir()), files_before)

    def test_local_file_audio_provider_uses_unknown_format_without_suffix(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input"
            input_path.write_bytes(b"user-owned audio")
            metadata = get_mock_metadata(str(input_path), platform="local")

            artifact = LocalFileAudioProvider().acquire(metadata)

        self.assertEqual(artifact.format, "unknown")
        self.assertFalse(artifact.temporary)

    def test_local_file_audio_provider_rejects_non_local_metadata(self) -> None:
        metadata = _youtube_metadata_with_raw({})

        with self.assertRaises(AudioAcquisitionError) as context:
            LocalFileAudioProvider().acquire(metadata)

        self.assertEqual(str(context.exception), "local audio input required")

    def test_local_file_audio_provider_rejects_empty_input(self) -> None:
        metadata = get_mock_metadata("", platform="local")

        with self.assertRaises(AudioAcquisitionError) as context:
            LocalFileAudioProvider().acquire(metadata)

        self.assertEqual(str(context.exception), "local audio input required")

    def test_local_file_audio_provider_reports_missing_file_without_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "signature-secret-token-hidden.m4a"
            metadata = get_mock_metadata(str(input_path), platform="local")

            with self.assertRaises(AudioAcquisitionError) as context:
                LocalFileAudioProvider().acquire(metadata)

        message = str(context.exception)
        self.assertEqual(message, "local audio input file not found")
        _assert_sensitive_audio_error_not_leaked(self, message)

    def test_local_file_audio_provider_rejects_directory(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata = get_mock_metadata(temp_dir, platform="local")

            with self.assertRaises(AudioAcquisitionError) as context:
                LocalFileAudioProvider().acquire(metadata)

        self.assertEqual(str(context.exception), "local audio input must be a file")

    def test_ytdlp_audio_provider_requires_explicit_permission(self) -> None:
        metadata = _youtube_metadata_with_raw({})
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = Path(temp_dir) / "permission-denied.m4a"
            fake_module, fake_ydl_class = _fake_audio_ytdlp_module(output_path)

            with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
                with self.assertRaises(AudioAcquisitionError) as context:
                    YtDlpAudioProvider(allow_audio_download=False).acquire(metadata)

        self.assertEqual(str(context.exception), "audio download permission required")
        self.assertEqual(fake_ydl_class.instances, [])
        self.assertFalse(output_path.exists())

    def test_ytdlp_audio_provider_rejects_non_youtube_metadata(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")

        with self.assertRaises(AudioAcquisitionError) as context:
            YtDlpAudioProvider(allow_audio_download=True).acquire(metadata)

        self.assertEqual(
            str(context.exception),
            "yt-dlp audio provider currently supports YouTube only",
        )

    def test_ytdlp_audio_provider_requires_existing_workspace(self) -> None:
        metadata = _youtube_metadata_with_raw({})

        with tempfile.TemporaryDirectory() as temp_dir:
            missing_workspace = Path(temp_dir) / "missing-signature-secret-token"
            with self.assertRaises(AudioAcquisitionError) as context:
                YtDlpAudioProvider(
                    workspace_dir=missing_workspace,
                    allow_audio_download=True,
                ).acquire(metadata)

        message = str(context.exception)
        self.assertEqual(message, "audio workspace directory required")
        _assert_sensitive_audio_error_not_leaked(self, message)

    def test_ytdlp_audio_provider_returns_temporary_audio_artifact(self) -> None:
        metadata = _youtube_metadata_with_raw({})
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            output_path = workspace / "video2knowledge-real123.m4a"
            fake_module, fake_ydl_class = _fake_audio_ytdlp_module(output_path)

            with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
                artifact = YtDlpAudioProvider(
                    workspace_dir=workspace,
                    allow_audio_download=True,
                    timeout_seconds=17,
                ).acquire(metadata)

            instance = fake_ydl_class.instances[0]
            self.assertEqual(
                instance.extract_calls,
                [(metadata.source_url, True)],
            )
            self.assertEqual(instance.opts["format"], "bestaudio")
            self.assertTrue(instance.opts["noplaylist"])
            self.assertFalse(instance.opts["writesubtitles"])
            self.assertFalse(instance.opts["writeautomaticsub"])
            self.assertFalse(instance.opts["writethumbnail"])
            self.assertEqual(instance.opts["postprocessors"], [])
            self.assertTrue(instance.opts["ignoreconfig"])
            self.assertEqual(instance.opts["socket_timeout"], 17)
            self.assertEqual(artifact.path, output_path.resolve())
            self.assertEqual(artifact.provider, YT_DLP_AUDIO_PROVIDER_ID)
            self.assertEqual(artifact.format, "m4a")
            self.assertTrue(artifact.temporary)

    def test_ytdlp_audio_provider_creates_unique_default_workspace(self) -> None:
        metadata = _youtube_metadata_with_raw({})
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            output_path = workspace / "video2knowledge-real123.m4a"
            fake_module, _ = _fake_audio_ytdlp_module(output_path)

            with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
                with mock.patch(
                    "app.audio.tempfile.mkdtemp",
                    return_value=str(workspace),
                ) as mkdtemp:
                    artifact = YtDlpAudioProvider(
                        allow_audio_download=True,
                    ).acquire(metadata)

            mkdtemp.assert_called_once_with(prefix="video2knowledge-audio-")
            self.assertEqual(artifact.path, output_path.resolve())
            self.assertTrue(artifact.temporary)

    def test_ytdlp_audio_provider_sanitizes_backend_failure(self) -> None:
        metadata = _youtube_metadata_with_raw({})
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_module, _ = _fake_audio_ytdlp_module(
                Path(temp_dir) / "unused.m4a",
                error=RuntimeError(
                    "https://example.com/audio?signature=secret&token=hidden stderr"
                ),
            )
            with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
                with self.assertRaises(AudioAcquisitionError) as context:
                    YtDlpAudioProvider(
                        workspace_dir=temp_dir,
                        allow_audio_download=True,
                    ).acquire(metadata)

        message = str(context.exception)
        self.assertEqual(message, "yt-dlp audio acquisition failed")
        _assert_sensitive_audio_error_not_leaked(self, message)

    def test_ytdlp_audio_provider_sanitizes_timeout(self) -> None:
        metadata = _youtube_metadata_with_raw({})
        with tempfile.TemporaryDirectory() as temp_dir:
            fake_module, _ = _fake_audio_ytdlp_module(
                Path(temp_dir) / "unused.m4a",
                error=TimeoutError("https://example.com/?signature=secret"),
            )
            with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
                with self.assertRaises(AudioAcquisitionError) as context:
                    YtDlpAudioProvider(
                        workspace_dir=temp_dir,
                        allow_audio_download=True,
                    ).acquire(metadata)

        self.assertEqual(str(context.exception), "yt-dlp audio acquisition timed out")

    def test_ytdlp_audio_provider_rejects_output_outside_workspace(self) -> None:
        metadata = _youtube_metadata_with_raw({})
        with tempfile.TemporaryDirectory() as temp_dir:
            external_output = Path(temp_dir).parent / "signature-secret-token-hidden.m4a"
            fake_module, _ = _fake_audio_ytdlp_module(
                external_output,
                create_output=False,
            )
            with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
                with self.assertRaises(AudioAcquisitionError) as context:
                    YtDlpAudioProvider(
                        workspace_dir=temp_dir,
                        allow_audio_download=True,
                    ).acquire(metadata)

        message = str(context.exception)
        self.assertEqual(message, "yt-dlp audio artifact missing")
        _assert_sensitive_audio_error_not_leaked(self, message)

    def test_ytdlp_audio_provider_rejects_missing_workspace_output(self) -> None:
        metadata = _youtube_metadata_with_raw({})
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_output = Path(temp_dir) / "missing.m4a"
            fake_module, _ = _fake_audio_ytdlp_module(
                missing_output,
                create_output=False,
            )
            with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
                with self.assertRaises(AudioAcquisitionError) as context:
                    YtDlpAudioProvider(
                        workspace_dir=temp_dir,
                        allow_audio_download=True,
                    ).acquire(metadata)

        self.assertEqual(str(context.exception), "yt-dlp audio artifact missing")

    def test_mock_audio_normalizer_does_not_create_media_file(self) -> None:
        artifact = AudioArtifact(
            path=Path("mock-audio.wav"),
            provider="mock_audio_provider",
            format="wav",
            temporary=True,
        )

        normalized = MockAudioNormalizer().normalize(artifact)

        self.assertEqual(normalized.provider, "mock_ffmpeg_normalizer")
        self.assertEqual(normalized.format, "wav")
        self.assertEqual(normalized.sample_rate, 16000)
        self.assertEqual(normalized.channels, 1)
        self.assertTrue(normalized.temporary)
        self.assertFalse(normalized.path.exists())

    def test_ffmpeg_audio_normalizer_reports_missing_ffmpeg(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.m4a"
            input_path.write_bytes(b"fake audio")
            artifact = _audio_artifact(input_path)

            with mock.patch("app.audio.shutil.which", return_value=None):
                with self.assertRaises(FfmpegNotFoundError) as context:
                    FfmpegAudioNormalizer(output_dir=temp_dir).normalize(artifact)

        self.assertEqual(str(context.exception), "ffmpeg not found")

    def test_ffmpeg_audio_normalizer_reports_missing_input(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "missing.m4a"
            artifact = _audio_artifact(input_path)

            with self.assertRaises(AudioProcessingError) as context:
                FfmpegAudioNormalizer(
                    output_dir=temp_dir,
                    ffmpeg_path="ffmpeg",
                ).normalize(artifact)

        self.assertEqual(str(context.exception), "audio input file not found")

    def test_ffmpeg_audio_normalizer_does_not_overwrite_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.m4a"
            output_path = Path(temp_dir) / "input-16k-mono.wav"
            input_path.write_bytes(b"fake audio")
            output_path.write_bytes(b"existing output")
            artifact = _audio_artifact(input_path)

            with mock.patch("app.audio.subprocess.run") as run:
                with self.assertRaises(AudioProcessingError) as context:
                    FfmpegAudioNormalizer(
                        output_dir=temp_dir,
                        ffmpeg_path="ffmpeg",
                    ).normalize(artifact)

        self.assertEqual(
            str(context.exception),
            "ffmpeg normalized output already exists",
        )
        run.assert_not_called()

    def test_ffmpeg_audio_normalizer_runs_expected_command(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.m4a"
            output_path = Path(temp_dir) / "input-16k-mono.wav"
            input_path.write_bytes(b"fake audio")
            artifact = _audio_artifact(input_path)

            def complete_process(command, **kwargs):
                output_path.write_bytes(b"fake wav")
                return subprocess.CompletedProcess(command, 0, "", "")

            with mock.patch("app.audio.subprocess.run", side_effect=complete_process) as run:
                normalized = FfmpegAudioNormalizer(
                    output_dir=temp_dir,
                    ffmpeg_path="ffmpeg",
                    timeout_seconds=12,
                ).normalize(artifact)

        command = run.call_args.args[0]
        self.assertEqual(command[0], "ffmpeg")
        self.assertEqual(command[1:4], ["-y", "-i", str(input_path)])
        self.assertIn("-vn", command)
        self.assertIn("-ac", command)
        self.assertIn("1", command)
        self.assertIn("-ar", command)
        self.assertIn("16000", command)
        self.assertIn("-acodec", command)
        self.assertIn("pcm_s16le", command)
        self.assertIn("-f", command)
        self.assertEqual(command[-2:], ["wav", str(output_path)])
        self.assertEqual(run.call_args.kwargs["timeout"], 12)
        self.assertTrue(run.call_args.kwargs["capture_output"])
        self.assertTrue(run.call_args.kwargs["text"])
        self.assertEqual(normalized.path, output_path)
        self.assertEqual(normalized.provider, "ffmpeg_audio_normalizer")
        self.assertEqual(normalized.format, "wav")
        self.assertEqual(normalized.sample_rate, 16000)
        self.assertEqual(normalized.channels, 1)

    def test_ffmpeg_audio_normalizer_wraps_non_zero_exit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.m4a"
            input_path.write_bytes(b"fake audio")
            artifact = _audio_artifact(input_path)
            process = subprocess.CompletedProcess(
                ["ffmpeg"],
                1,
                "",
                "signature=secret token=hidden stderr",
            )

            with mock.patch("app.audio.subprocess.run", return_value=process):
                with self.assertRaises(AudioProcessingError) as context:
                    FfmpegAudioNormalizer(
                        output_dir=temp_dir,
                        ffmpeg_path="ffmpeg",
                    ).normalize(artifact)

        message = str(context.exception)
        self.assertEqual(message, "ffmpeg audio normalization failed")
        _assert_sensitive_audio_error_not_leaked(self, message)

    def test_ffmpeg_audio_normalizer_wraps_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.m4a"
            input_path.write_bytes(b"fake audio")
            artifact = _audio_artifact(input_path)

            with mock.patch(
                "app.audio.subprocess.run",
                side_effect=subprocess.TimeoutExpired(["ffmpeg", "secret"], 12),
            ):
                with self.assertRaises(AudioProcessingError) as context:
                    FfmpegAudioNormalizer(
                        output_dir=temp_dir,
                        ffmpeg_path="ffmpeg",
                        timeout_seconds=12,
                    ).normalize(artifact)

        message = str(context.exception)
        self.assertEqual(message, "ffmpeg audio normalization timed out")
        _assert_sensitive_audio_error_not_leaked(self, message)

    def test_ffmpeg_audio_normalizer_reports_missing_output(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "input.m4a"
            input_path.write_bytes(b"fake audio")
            artifact = _audio_artifact(input_path)
            process = subprocess.CompletedProcess(["ffmpeg"], 0, "", "")

            with mock.patch("app.audio.subprocess.run", return_value=process):
                with self.assertRaises(AudioProcessingError) as context:
                    FfmpegAudioNormalizer(
                        output_dir=temp_dir,
                        ffmpeg_path="ffmpeg",
                    ).normalize(artifact)

        self.assertEqual(
            str(context.exception),
            "ffmpeg normalized output missing",
        )

    def test_ffmpeg_audio_normalizer_errors_do_not_leak_sensitive_input(self) -> None:
        sensitive_name = "input-signature-secret-token-hidden.m4a"
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / sensitive_name
            input_path.write_bytes(b"fake audio")
            artifact = _audio_artifact(input_path)
            process = subprocess.CompletedProcess(["ffmpeg"], 1, "", "secret stderr")

            with mock.patch("app.audio.subprocess.run", return_value=process):
                with self.assertRaises(AudioProcessingError) as context:
                    FfmpegAudioNormalizer(
                        output_dir=temp_dir,
                        ffmpeg_path="ffmpeg",
                    ).normalize(artifact)

        message = str(context.exception)
        self.assertEqual(message, "ffmpeg audio normalization failed")
        _assert_sensitive_audio_error_not_leaked(self, message)

    def test_real_fallback_preserves_platform_access_error(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {"subtitles": {"zh-CN": [{"ext": "vtt", "url": "https://example.com/zh.vtt"}]}}
        )

        for status_code in [429, 403]:
            with self.subTest(status_code=status_code):
                error = HTTPError(
                    "https://example.com/zh.vtt",
                    status_code,
                    "Platform Access Error",
                    None,
                    None,
                )
                with mock.patch("app.transcript.urlopen", side_effect=error):
                    with mock.patch("app.transcript.MockAudioProvider") as audio_provider:
                        with mock.patch("app.transcript.MockAudioNormalizer") as normalizer:
                            with self.assertRaises(PlatformAccessError):
                                acquire_transcript_with_provider(
                                    metadata,
                                    provider_name="real-fallback",
                                )

                audio_provider.assert_not_called()
                normalizer.assert_not_called()

    def test_real_fallback_preserves_network_access_error(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {"subtitles": {"zh-CN": [{"ext": "vtt", "url": "https://example.com/zh.vtt"}]}}
        )

        with mock.patch("app.transcript.urlopen", side_effect=URLError("network secret")):
            with mock.patch("app.transcript.MockAudioProvider") as audio_provider:
                with mock.patch("app.transcript.MockAudioNormalizer") as normalizer:
                    with self.assertRaises(NetworkAccessError):
                        acquire_transcript_with_provider(metadata, provider_name="real-fallback")

        audio_provider.assert_not_called()
        normalizer.assert_not_called()

    def test_real_fallback_preserves_generic_transcript_error_without_audio(self) -> None:
        metadata = _youtube_metadata_with_raw(
            {"subtitles": {"zh-CN": [{"ext": "vtt", "url": "https://example.com/zh.vtt"}]}}
        )

        with mock.patch("app.transcript.fetch_text", return_value="WEBVTT\n\n"):
            with mock.patch("app.transcript.MockAudioProvider") as audio_provider:
                with mock.patch("app.transcript.MockAudioNormalizer") as normalizer:
                    with self.assertRaises(TranscriptProviderError):
                        acquire_transcript_with_provider(metadata, provider_name="real-fallback")

        audio_provider.assert_not_called()
        normalizer.assert_not_called()

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


def _fake_audio_ytdlp_module(
    output_path: Path,
    error: Exception | None = None,
    create_output: bool = True,
):
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
            if error is not None:
                raise error
            if create_output:
                output_path.write_bytes(b"mock audio artifact")
            return {"requested_downloads": [{"filepath": str(output_path)}]}

        def prepare_filename(self, info):
            return str(output_path)

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


def _audio_artifact(path: Path) -> AudioArtifact:
    return AudioArtifact(
        path=path,
        provider="test_audio_provider",
        format=path.suffix.lstrip(".") or "unknown",
        temporary=True,
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


def _assert_sensitive_audio_error_not_leaked(
    test_case: unittest.TestCase,
    output: str,
) -> None:
    for sensitive_value in [
        "signature",
        "token",
        "secret",
        "hidden",
        "stderr",
        "ffmpeg -y",
        "input-signature-secret-token-hidden",
    ]:
        test_case.assertNotIn(sensitive_value, output)


if __name__ == "__main__":
    unittest.main()
