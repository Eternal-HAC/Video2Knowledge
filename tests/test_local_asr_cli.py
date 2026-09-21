"""Fully mocked tests for the explicit local ASR CLI command.

Nothing in this module runs ffmpeg, faster-whisper, a model download, a
provider, or any network call. The orchestration boundary and the workspace are
mocked; the parser, the neutral-metadata construction, the dependency wiring,
and both stdout renderings are exercised for real.
"""

from __future__ import annotations

import contextlib
import hashlib
import io
import json
import os
import tempfile
import traceback
import unittest
from pathlib import Path
from unittest import mock

import app.cli as cli
from app.audio import FfmpegAudioNormalizer
from app.cli import (
    OFFLINE_MODEL_HINT,
    _LOCAL_MEDIA_INPUT_REQUIRED_MESSAGE,
    build_parser,
    main,
    render_local_transcript_json,
    render_local_transcript_text,
    run_transcribe_local,
)
from app.errors import (
    AudioAcquisitionError,
    AudioProcessingError,
    FfmpegNotFoundError,
    LocalTranscriptionError,
)
from app.models import TranscriptResult, TranscriptSegment, VideoMetadata, VideoSource
from app.pipeline import transcribe_local_media
from app.whisper import FASTER_WHISPER_PROVIDER_ID, FasterWhisperBackend


def _result(
    provider: str = FASTER_WHISPER_PROVIDER_ID,
    attempted: list[str] | None = None,
    segments: list[TranscriptSegment] | None = None,
) -> TranscriptResult:
    return TranscriptResult(
        segments=(
            segments
            if segments is not None
            else [
                TranscriptSegment("00:00:00.000", "00:00:01.500", "Hello world."),
                TranscriptSegment("00:00:01.500", "00:00:03.000", "Second line."),
            ]
        ),
        provider=provider,
        attempted_providers=list(attempted) if attempted is not None else [provider],
    )


def _run_cli(argv: list[str]) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        exit_code = main(argv)
    return exit_code, stdout.getvalue(), stderr.getvalue()


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


# The approved two-line offline failure contract, written out literally so a
# drift in the exported hint constant is caught rather than mirrored.
OFFLINE_HINT_LINE = (
    "Hint: offline model loading is enabled; use an existing cached model, "
    "a local model directory, or explicitly pass --allow-model-download."
)
OFFLINE_FAILURE_STDERR = (
    "Error: local transcription failed\n" + OFFLINE_HINT_LINE + "\n"
)


class LocalAsrCliParserTests(unittest.TestCase):
    def test_help_lists_the_approved_grammar(self) -> None:
        stdout = io.StringIO()

        with contextlib.redirect_stdout(stdout):
            with self.assertRaises(SystemExit) as context:
                main(["transcribe-local", "--help"])

        output = stdout.getvalue()
        self.assertEqual(context.exception.code, 0)
        self.assertIn("path", output)
        for flag in (
            "--model",
            "--device",
            "--compute-type",
            "--language",
            "--ffmpeg-path",
            "--allow-model-download",
            "--format",
        ):
            with self.subTest(flag=flag):
                self.assertIn(flag, output)
        self.assertIn("{text,json}", output)
        self.assertNotIn("--output-dir", output)

    def test_parser_defaults_match_the_approved_contract(self) -> None:
        args = build_parser().parse_args(["transcribe-local", "clip.m4a"])

        self.assertEqual(args.command, "transcribe-local")
        self.assertEqual(args.path, "clip.m4a")
        self.assertEqual(args.model, "small")
        self.assertEqual(args.device, "cpu")
        self.assertEqual(args.compute_type, "int8")
        self.assertIsNone(args.language)
        self.assertIsNone(args.ffmpeg_path)
        self.assertFalse(args.allow_model_download)
        self.assertEqual(args.format, "text")

    def test_parser_accepts_every_documented_override(self) -> None:
        args = build_parser().parse_args(
            [
                "transcribe-local",
                "clip.m4a",
                "--model",
                "medium",
                "--device",
                "cuda",
                "--compute-type",
                "float16",
                "--language",
                "zh",
                "--ffmpeg-path",
                "C:/tools/ffmpeg.exe",
                "--allow-model-download",
                "--format",
                "json",
            ]
        )

        self.assertEqual(args.model, "medium")
        self.assertEqual(args.device, "cuda")
        self.assertEqual(args.compute_type, "float16")
        self.assertEqual(args.language, "zh")
        self.assertEqual(args.ffmpeg_path, "C:/tools/ffmpeg.exe")
        self.assertTrue(args.allow_model_download)
        self.assertEqual(args.format, "json")

    def test_path_argument_is_required(self) -> None:
        stderr = io.StringIO()

        with contextlib.redirect_stderr(stderr):
            with self.assertRaises(SystemExit) as context:
                main(["transcribe-local"])

        self.assertEqual(context.exception.code, 2)
        self.assertIn("path", stderr.getvalue())

    def test_unknown_and_missing_flags_are_rejected(self) -> None:
        for argv in (
            ["transcribe-local", "clip.m4a", "--output-dir", "output/markdown"],
            ["transcribe-local", "clip.m4a", "--format", "markdown"],
            ["transcribe-local", "clip.m4a", "--transcript-provider", "mock"],
        ):
            with self.subTest(argv=argv):
                with contextlib.redirect_stderr(io.StringIO()):
                    with self.assertRaises(SystemExit) as context:
                        main(argv)
                self.assertEqual(context.exception.code, 2)

    def test_import_url_grammar_is_unchanged(self) -> None:
        args = build_parser().parse_args(["import-url", "https://example.com/watch?v=mock"])

        self.assertEqual(args.url, "https://example.com/watch?v=mock")
        self.assertEqual(args.output_dir, "output/markdown")
        self.assertEqual(args.metadata_provider, "mock")
        self.assertEqual(args.transcript_provider, "mock")


class LocalAsrCliInputTests(unittest.TestCase):
    def test_url_input_is_rejected_before_orchestration(self) -> None:
        with mock.patch("app.cli.transcribe_local_media") as orchestrate:
            exit_code, stdout, stderr = _run_cli(
                ["transcribe-local", "https://example.com/watch?v=mock"]
            )

        orchestrate.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Error: local media file path required\n")

    def test_classified_url_source_is_rejected(self) -> None:
        source = VideoSource(
            raw_input="https://www.youtube.com/watch?v=mock",
            source_type="url",
            platform="youtube",
        )
        with mock.patch("app.cli.resolve_video_source", return_value=source) as resolve:
            with mock.patch("app.cli.transcribe_local_media") as orchestrate:
                exit_code, _, stderr = _run_cli(["transcribe-local", "youtube.com.evil.test"])

        resolve.assert_called_once_with("youtube.com.evil.test")
        orchestrate.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertEqual(stderr, "Error: local media file path required\n")

    def test_malformed_url_returns_stable_error_without_traceback(self) -> None:
        malformed_url = "http://[::1"

        with mock.patch("app.cli.transcribe_local_media") as orchestrate:
            exit_code, stdout, stderr = _run_cli(
                ["transcribe-local", malformed_url]
            )

        orchestrate.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Error: local media file path required\n")
        self.assertNotIn("Traceback", stderr)
        self.assertNotIn("ValueError", stderr)
        self.assertNotIn("Invalid IPv6 URL", stderr)
        self.assertNotIn(malformed_url, stderr)
        self.assertNotIn("Traceback", stdout)

    def test_parser_failure_inside_classification_is_also_stable(self) -> None:
        with mock.patch(
            "app.cli.resolve_video_source",
            side_effect=ValueError("Invalid IPv6 URL"),
        ) as resolve:
            with mock.patch("app.cli.transcribe_local_media") as orchestrate:
                exit_code, stdout, stderr = _run_cli(
                    ["transcribe-local", "not-a-local-file"]
                )

        resolve.assert_called_once_with("not-a-local-file")
        orchestrate.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Error: local media file path required\n")
        self.assertNotIn("Traceback", stderr)
        self.assertNotIn("Invalid IPv6 URL", stderr)

    def test_classification_error_does_not_change_propagation_rules(self) -> None:
        for error in (KeyboardInterrupt(), SystemExit(7)):
            with self.subTest(error=type(error).__name__):
                # Only ValueError is a classification failure; control-flow
                # exceptions raised during classification must still propagate.
                with mock.patch("app.cli.resolve_video_source", side_effect=error):
                    with mock.patch("app.cli.transcribe_local_media") as orchestrate:
                        with contextlib.redirect_stderr(io.StringIO()) as stderr:
                            with self.assertRaises(type(error)):
                                main(["transcribe-local", "clip.m4a"])

                orchestrate.assert_not_called()
                self.assertEqual(stderr.getvalue(), "")

    def test_classification_error_text_is_the_shared_constant(self) -> None:
        self.assertEqual(
            _LOCAL_MEDIA_INPUT_REQUIRED_MESSAGE,
            "local media file path required",
        )

    def test_classification_uses_existing_resolver(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch(
                "app.cli.resolve_video_source",
                wraps=cli.resolve_video_source,
            ) as resolve:
                with mock.patch("app.cli.transcribe_local_media", return_value=_result()):
                    exit_code, _, _ = _run_cli(["transcribe-local", str(input_path)])

        self.assertEqual(exit_code, 0)
        resolve.assert_called_once_with(str(input_path))

    def test_inaccessible_user_file_is_sanitized_through_cli_orchestration(self) -> None:
        private_path = r"C:\private\media\secret-recording.m4a"
        stat_error = PermissionError(f"access denied: {private_path}")

        with mock.patch.object(Path, "stat", side_effect=stat_error):
            with self.assertRaises(AudioAcquisitionError) as context:
                run_transcribe_local(private_path)

        formatted = "".join(
            traceback.format_exception(
                type(context.exception),
                context.exception,
                context.exception.__traceback__,
            )
        )
        self.assertEqual(str(context.exception), "local audio input inaccessible")
        self.assertIsNone(context.exception.__cause__)
        self.assertTrue(context.exception.__suppress_context__)
        self.assertNotIn(private_path, formatted)
        self.assertNotIn("access denied", formatted)

        with mock.patch.object(Path, "stat", side_effect=stat_error):
            exit_code, stdout, stderr = _run_cli(["transcribe-local", private_path])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Error: local audio input inaccessible\n")
        self.assertNotIn(private_path, stderr)
        self.assertNotIn("access denied", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_missing_user_file_traceback_is_sanitized_through_cli_orchestration(
        self,
    ) -> None:
        private_path = r"C:\private\media\secret-recording.m4a"
        sentinel = "missing-file-sentinel"
        stat_error = FileNotFoundError(f"{sentinel}: {private_path}")

        with mock.patch.object(Path, "stat", side_effect=stat_error):
            with self.assertRaises(AudioAcquisitionError) as context:
                run_transcribe_local(private_path)

        formatted = "".join(
            traceback.format_exception(
                type(context.exception),
                context.exception,
                context.exception.__traceback__,
            )
        )
        self.assertEqual(str(context.exception), "local audio input file not found")
        self.assertIsNone(context.exception.__cause__)
        self.assertTrue(context.exception.__suppress_context__)
        self.assertNotIn(private_path, formatted)
        self.assertNotIn(sentinel, formatted)
        self.assertNotIn("FileNotFoundError", formatted)

        with mock.patch.object(Path, "stat", side_effect=stat_error):
            exit_code, stdout, stderr = _run_cli(["transcribe-local", private_path])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, "Error: local audio input file not found\n")
        self.assertNotIn(private_path, stderr)
        self.assertNotIn(sentinel, stderr)
        self.assertNotIn("Traceback", stderr)

    def test_neutral_metadata_is_built_privately(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "user-clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch(
                "app.cli.transcribe_local_media",
                return_value=_result(),
            ) as orchestrate:
                with mock.patch(
                    "app.downloader.get_mock_metadata",
                    side_effect=AssertionError("mock metadata must not be used"),
                ) as mock_metadata:
                    exit_code, _, stderr = _run_cli(
                        ["transcribe-local", str(input_path)]
                    )

        mock_metadata.assert_not_called()
        self.assertEqual(exit_code, 0, stderr)
        metadata = orchestrate.call_args.args[0]
        self.assertIsInstance(metadata, VideoMetadata)
        self.assertEqual(
            metadata,
            VideoMetadata(
                title="user-clip",
                platform="local",
                source_url=str(input_path),
                author="",
                published_at="",
                duration="",
                language="",
                tags=[],
                status="local_input",
                raw_metadata=None,
            ),
        )
        self.assertEqual(metadata.title, Path(input_path).stem)
        self.assertEqual(metadata.platform, "local")
        self.assertEqual(metadata.source_url, str(input_path))
        self.assertEqual(metadata.author, "")
        self.assertEqual(metadata.published_at, "")
        self.assertEqual(metadata.duration, "")
        self.assertEqual(metadata.language, "")
        self.assertEqual(metadata.tags, [])
        self.assertEqual(metadata.status, "local_input")
        self.assertIsNone(metadata.raw_metadata)
        self.assertFalse(hasattr(cli, "get_mock_metadata"))

    def test_metadata_title_falls_back_to_a_neutral_label(self) -> None:
        title = cli._build_local_metadata("").title

        self.assertEqual(title, "Local media")

    def test_metadata_title_prefers_the_path_stem(self) -> None:
        for path, expected in (
            ("clip.m4a", "clip"),
            (r"C:\media\My Talk.mp4", "My Talk"),
            ("user-owned.mkv", "user-owned"),
        ):
            with self.subTest(path=path):
                self.assertEqual(cli._build_local_metadata(path).title, expected)


class LocalAsrCliDependencyTests(unittest.TestCase):
    def test_default_dependencies_are_offline_cpu_int8(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch(
                "app.cli.transcribe_local_media",
                return_value=_result(),
            ) as orchestrate:
                exit_code, _, stderr = _run_cli(["transcribe-local", str(input_path)])

        self.assertEqual(exit_code, 0, stderr)
        backend = orchestrate.call_args.kwargs["whisper_backend"]
        self.assertIsInstance(backend, FasterWhisperBackend)
        self.assertEqual(backend.model_size, "small")
        self.assertEqual(backend.device, "cpu")
        self.assertEqual(backend.compute_type, "int8")
        self.assertIsNone(backend.language)
        self.assertTrue(backend.local_files_only)

    def test_overridden_dependencies_pass_through(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch(
                "app.cli.transcribe_local_media",
                return_value=_result(),
            ) as orchestrate:
                exit_code, _, stderr = _run_cli(
                    [
                        "transcribe-local",
                        str(input_path),
                        "--model",
                        "medium",
                        "--device",
                        "cuda",
                        "--compute-type",
                        "float16",
                        "--language",
                        "zh",
                        "--allow-model-download",
                    ]
                )

        self.assertEqual(exit_code, 0, stderr)
        backend = orchestrate.call_args.kwargs["whisper_backend"]
        self.assertEqual(backend.model_size, "medium")
        self.assertEqual(backend.device, "cuda")
        self.assertEqual(backend.compute_type, "float16")
        self.assertEqual(backend.language, "zh")
        self.assertFalse(backend.local_files_only)

    def test_local_model_directory_is_passed_to_the_backend_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            model_path = Path(temp_dir) / "user-model"
            model_path.mkdir()
            (model_path / "tokenizer.json").write_text("{}", encoding="utf-8")

            with mock.patch(
                "app.cli.transcribe_local_media",
                return_value=_result(),
            ) as orchestrate:
                exit_code, _, stderr = _run_cli(
                    [
                        "transcribe-local",
                        str(input_path),
                        "--model",
                        str(model_path),
                    ]
                )

        self.assertEqual(exit_code, 0, stderr)
        backend = orchestrate.call_args.kwargs["whisper_backend"]
        # The CLI must not resolve, copy, or rewrite the supplied model path;
        # offline resolution belongs to the backend, which never runs here.
        self.assertEqual(backend.model_size, str(model_path))
        self.assertTrue(backend.local_files_only)

    def test_model_policy_is_flag_driven_not_environment_driven(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch.dict(
                os.environ,
                {"HF_HUB_OFFLINE": "0", "VIDEO2KNOWLEDGE_ALLOW_MODEL_DOWNLOAD": "1"},
            ):
                with mock.patch(
                    "app.cli.transcribe_local_media",
                    return_value=_result(),
                ) as orchestrate:
                    exit_code, _, _ = _run_cli(["transcribe-local", str(input_path)])

        self.assertEqual(exit_code, 0)
        self.assertTrue(orchestrate.call_args.kwargs["whisper_backend"].local_files_only)

    def test_command_delegates_to_existing_orchestration_once(self) -> None:
        self.assertIs(cli.transcribe_local_media, transcribe_local_media)

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch(
                "app.cli.transcribe_local_media",
                return_value=_result(),
            ) as orchestrate:
                exit_code, _, _ = _run_cli(["transcribe-local", str(input_path)])

        self.assertEqual(exit_code, 0)
        orchestrate.assert_called_once()
        self.assertEqual(orchestrate.call_args.args[0].source_url, str(input_path))
        self.assertNotIn("audio_provider", orchestrate.call_args.kwargs)

    def test_explicit_ffmpeg_path_is_injected_into_the_normalizer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            ffmpeg_path = Path(temp_dir) / "ffmpeg.exe"
            ffmpeg_path.write_bytes(b"fake executable")
            workspace_path = Path(temp_dir) / "workspace"
            workspace_path.mkdir()

            with mock.patch(
                "app.cli.transcribe_local_media",
                return_value=_result(),
            ) as orchestrate:
                exit_code, _, stderr = _run_cli(
                    [
                        "transcribe-local",
                        str(input_path),
                        "--ffmpeg-path",
                        str(ffmpeg_path),
                    ]
                )

            normalizer = orchestrate.call_args.kwargs["normalizer_factory"](
                workspace_path
            )

        self.assertEqual(exit_code, 0, stderr)
        self.assertIsInstance(normalizer, FfmpegAudioNormalizer)
        self.assertEqual(normalizer.output_dir, workspace_path)
        self.assertEqual(normalizer.ffmpeg_path, str(ffmpeg_path))

    def test_absent_ffmpeg_path_keeps_existing_path_discovery(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            workspace_path = Path(temp_dir) / "workspace"
            workspace_path.mkdir()

            with mock.patch(
                "app.cli.transcribe_local_media",
                return_value=_result(),
            ) as orchestrate:
                exit_code, _, stderr = _run_cli(["transcribe-local", str(input_path)])

            normalizer = orchestrate.call_args.kwargs["normalizer_factory"](
                workspace_path
            )

            self.assertIsNone(normalizer.ffmpeg_path)
            self.assertEqual(normalizer.output_dir, workspace_path)
            with mock.patch(
                "app.audio.shutil.which",
                return_value=str(Path(temp_dir) / "ffmpeg.exe"),
            ) as which:
                self.assertEqual(
                    normalizer._resolve_ffmpeg(),
                    str(Path(temp_dir) / "ffmpeg.exe"),
                )
            which.assert_called_once_with("ffmpeg")
            with mock.patch("app.audio.shutil.which", return_value=None):
                with self.assertRaises(FfmpegNotFoundError):
                    normalizer._resolve_ffmpeg()

        self.assertEqual(exit_code, 0, stderr)

    def test_missing_or_directory_ffmpeg_path_is_sanitized(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            private_dir = Path(temp_dir) / "private-secret-tools"
            private_dir.mkdir()
            missing_executable = private_dir / "ffmpeg-secret-name.exe"

            with mock.patch("app.cli.transcribe_local_media") as orchestrate:
                missing_code, missing_stdout, missing_stderr = _run_cli(
                    [
                        "transcribe-local",
                        str(input_path),
                        "--ffmpeg-path",
                        str(missing_executable),
                    ]
                )
                directory_code, _, directory_stderr = _run_cli(
                    [
                        "transcribe-local",
                        str(input_path),
                        "--ffmpeg-path",
                        str(private_dir),
                    ]
                )

        orchestrate.assert_not_called()
        self.assertEqual(missing_code, 1)
        self.assertEqual(directory_code, 1)
        self.assertEqual(missing_stdout, "")
        self.assertEqual(missing_stderr, "Error: ffmpeg not found\n")
        self.assertEqual(directory_stderr, "Error: ffmpeg not found\n")
        self.assertNotIn("private-secret-tools", missing_stderr)
        self.assertNotIn("ffmpeg-secret-name", missing_stderr)
        self.assertNotIn("Traceback", missing_stderr)

    def test_explicit_ffmpeg_failure_reuses_the_shared_stable_message(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            private_dir = Path(temp_dir) / "private-secret-tools"
            private_dir.mkdir()

            with mock.patch("app.cli.transcribe_local_media") as orchestrate:
                exit_code, stdout, stderr = _run_cli(
                    [
                        "transcribe-local",
                        str(input_path),
                        "--ffmpeg-path",
                        str(private_dir / "ffmpeg-secret-name.exe"),
                    ]
                )

        orchestrate.assert_not_called()
        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        # Exactly the message the existing ffmpeg boundary already uses; this
        # command must not introduce a second wording for the same failure.
        self.assertEqual(stderr, "Error: ffmpeg not found\n")
        self.assertEqual(cli._FFMPEG_EXECUTABLE_REQUIRED_MESSAGE, "ffmpeg not found")
        self.assertNotIn("executable", stderr)
        self.assertNotIn("Traceback", stderr)


class LocalAsrCliOutputTests(unittest.TestCase):
    def test_default_text_stdout_contains_only_transcript_fields(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch("app.cli.transcribe_local_media", return_value=_result()):
                exit_code, stdout, stderr = _run_cli(["transcribe-local", str(input_path)])

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            stdout,
            "Provider: faster_whisper\n"
            "Attempted providers: faster_whisper\n"
            "[00:00:00.000 --> 00:00:01.500] Hello world.\n"
            "[00:00:01.500 --> 00:00:03.000] Second line.\n",
        )

    def test_json_stdout_matches_the_transcript_result_schema(self) -> None:
        segments = [TranscriptSegment("00:00:00.000", "00:00:02.000", "中文字幕")]
        result = _result(segments=segments)

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch("app.cli.transcribe_local_media", return_value=result):
                exit_code, stdout, stderr = _run_cli(
                    ["transcribe-local", str(input_path), "--format", "json"]
                )

        payload = json.loads(stdout)
        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertEqual(
            set(payload),
            {"provider", "attempted_providers", "segments"},
        )
        self.assertEqual(payload["provider"], FASTER_WHISPER_PROVIDER_ID)
        self.assertEqual(payload["attempted_providers"], [FASTER_WHISPER_PROVIDER_ID])
        self.assertEqual(
            payload["segments"],
            [{"start": "00:00:00.000", "end": "00:00:02.000", "text": "中文字幕"}],
        )
        self.assertEqual(set(payload["segments"][0]), {"start", "end", "text"})
        self.assertIn("中文字幕", stdout)
        self.assertNotIn("\\u4e2d", stdout)

    def test_renderings_reflect_the_returned_provider_fields(self) -> None:
        result = _result(
            provider="custom_provider",
            attempted=["first_provider", "custom_provider"],
        )

        text = render_local_transcript_text(result)
        payload = json.loads(render_local_transcript_json(result))

        self.assertTrue(text.startswith("Provider: custom_provider\n"))
        self.assertIn(
            "Attempted providers: first_provider, custom_provider\n",
            text,
        )
        self.assertEqual(payload["provider"], "custom_provider")
        self.assertEqual(
            payload["attempted_providers"],
            ["first_provider", "custom_provider"],
        )

    def test_empty_segment_lists_render_without_inventing_content(self) -> None:
        result = _result()
        empty = TranscriptResult(
            segments=[],
            provider=result.provider,
            attempted_providers=list(result.attempted_providers),
        )

        self.assertEqual(
            render_local_transcript_text(empty),
            "Provider: faster_whisper\nAttempted providers: faster_whisper",
        )
        self.assertEqual(
            json.loads(render_local_transcript_json(empty))["segments"],
            [],
        )

    def test_default_format_is_not_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch("app.cli.transcribe_local_media", return_value=_result()):
                _, stdout, _ = _run_cli(["transcribe-local", str(input_path)])

        with self.assertRaises(json.JSONDecodeError):
            json.loads(stdout)


class LocalAsrCliErrorTests(unittest.TestCase):
    def test_business_errors_print_one_stable_line_and_return_one(self) -> None:
        cases = [
            AudioAcquisitionError("local media file path required"),
            AudioAcquisitionError("local audio input file not found"),
            AudioAcquisitionError("local audio input must be a file"),
            AudioAcquisitionError("local audio input must be user-owned"),
            AudioAcquisitionError("local audio input required"),
            AudioProcessingError("ffmpeg audio normalization failed"),
            AudioProcessingError("audio workspace cleanup failed"),
            FfmpegNotFoundError("ffmpeg not found"),
            LocalTranscriptionError("faster-whisper is not installed"),
            LocalTranscriptionError("local transcription produced no segments"),
        ]

        for error in cases:
            with self.subTest(error=str(error)):
                with mock.patch("app.cli.transcribe_local_media", side_effect=error):
                    exit_code, stdout, stderr = _run_cli(
                        ["transcribe-local", "clip.m4a"]
                    )

                self.assertEqual(exit_code, 1)
                self.assertEqual(stdout, "")
                self.assertEqual(stderr, f"Error: {error}\n")
                self.assertNotIn("Traceback", stderr)

    def test_error_output_never_includes_cause_paths_or_secrets(self) -> None:
        error = LocalTranscriptionError("local transcription failed")
        error.__cause__ = RuntimeError("C:\\private\\model-cache token=secret")

        with mock.patch("app.cli.transcribe_local_media", side_effect=error):
            exit_code, stdout, stderr = _run_cli(["transcribe-local", "clip.m4a"])

        self.assertEqual(exit_code, 1)
        self.assertEqual(stdout, "")
        self.assertEqual(stderr, OFFLINE_FAILURE_STDERR)
        self.assertNotIn("C:\\private", stderr)
        self.assertNotIn("token=secret", stderr)
        self.assertNotIn("Traceback", stderr)

    def test_offline_hint_is_appended_only_for_the_offline_failure(self) -> None:
        failure = LocalTranscriptionError("local transcription failed")

        with mock.patch("app.cli.transcribe_local_media", side_effect=failure):
            offline_code, offline_stdout, offline_stderr = _run_cli(
                ["transcribe-local", "clip.m4a"]
            )
            allowed_code, _, allowed_stderr = _run_cli(
                ["transcribe-local", "clip.m4a", "--allow-model-download"]
            )

        other_failure = LocalTranscriptionError("faster-whisper is not installed")
        with mock.patch("app.cli.transcribe_local_media", side_effect=other_failure):
            other_code, _, other_stderr = _run_cli(["transcribe-local", "clip.m4a"])

        self.assertEqual(offline_code, 1)
        self.assertEqual(offline_stdout, "")
        self.assertEqual(
            offline_stderr,
            "Error: local transcription failed\n"
            "Hint: offline model loading is enabled; use an existing cached "
            "model, a local model directory, or explicitly pass "
            "--allow-model-download.\n",
        )
        self.assertEqual(offline_stderr, OFFLINE_FAILURE_STDERR)
        self.assertEqual(
            offline_stderr.splitlines(),
            ["Error: local transcription failed", OFFLINE_HINT_LINE],
        )
        self.assertEqual(offline_stderr.count("\n"), 2)
        self.assertTrue(offline_stderr.endswith("--allow-model-download.\n"))
        self.assertEqual(OFFLINE_MODEL_HINT, OFFLINE_HINT_LINE)
        self.assertEqual(allowed_code, 1)
        self.assertEqual(allowed_stderr, "Error: local transcription failed\n")
        self.assertEqual(other_code, 1)
        self.assertEqual(other_stderr, "Error: faster-whisper is not installed\n")

    def test_keyboard_interrupt_propagates_without_output(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch(
            "app.cli.transcribe_local_media",
            side_effect=KeyboardInterrupt(),
        ):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(KeyboardInterrupt):
                    main(["transcribe-local", "clip.m4a"])

        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_system_exit_propagates_without_output(self) -> None:
        stdout = io.StringIO()
        stderr = io.StringIO()

        with mock.patch("app.cli.transcribe_local_media", side_effect=SystemExit(7)):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(SystemExit) as context:
                    main(["transcribe-local", "clip.m4a"])

        self.assertEqual(context.exception.code, 7)
        self.assertEqual(stdout.getvalue(), "")
        self.assertEqual(stderr.getvalue(), "")

    def test_unexpected_errors_are_not_converted_to_stable_output(self) -> None:
        with mock.patch(
            "app.cli.transcribe_local_media",
            side_effect=ValueError("unexpected failure"),
        ):
            with contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(ValueError):
                    main(["transcribe-local", "clip.m4a"])


class LocalAsrCliSideEffectTests(unittest.TestCase):
    def test_user_input_and_its_directory_are_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "user-clip.m4a"
            input_path.write_bytes(b"user-owned media")
            input_hash = _sha256(input_path)
            listing_before = sorted(path.name for path in Path(temp_dir).iterdir())

            with mock.patch("app.cli.transcribe_local_media", return_value=_result()):
                text_code, _, _ = _run_cli(["transcribe-local", str(input_path)])
                json_code, _, _ = _run_cli(
                    ["transcribe-local", str(input_path), "--format", "json"]
                )

            listing_after = sorted(path.name for path in Path(temp_dir).iterdir())
            final_hash = _sha256(input_path)

        self.assertEqual((text_code, json_code), (0, 0))
        self.assertEqual(final_hash, input_hash)
        self.assertEqual(listing_after, listing_before)
        self.assertEqual(listing_after, ["user-clip.m4a"])

    def test_command_does_not_run_the_import_pipeline_or_writer(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")

            with mock.patch("app.cli.transcribe_local_media", return_value=_result()):
                with mock.patch(
                    "app.cli.run_import_pipeline",
                    side_effect=AssertionError("import pipeline must not run"),
                ) as pipeline:
                    with mock.patch(
                        "app.exporter.obsidian.export_markdown",
                        side_effect=AssertionError("export must not run"),
                    ) as export:
                        exit_code, _, stderr = _run_cli(
                            ["transcribe-local", str(input_path)]
                        )

        self.assertEqual(exit_code, 0, stderr)
        pipeline.assert_not_called()
        export.assert_not_called()

    def test_run_transcribe_local_returns_the_backend_result_unchanged(self) -> None:
        result = _result()

        with tempfile.TemporaryDirectory() as temp_dir:
            input_path = Path(temp_dir) / "clip.m4a"
            input_path.write_bytes(b"user media")
            with mock.patch("app.cli.transcribe_local_media", return_value=result):
                returned = run_transcribe_local(str(input_path))

        self.assertIs(returned, result)


class ImportUrlRegressionTests(unittest.TestCase):
    def test_import_url_still_writes_markdown(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = _run_cli(
                [
                    "import-url",
                    "https://example.com/watch?v=mock",
                    "--metadata-provider",
                    "mock",
                    "--transcript-provider",
                    "mock",
                    "--output-dir",
                    temp_dir,
                ]
            )
            markdown_files = sorted(Path(temp_dir).glob("*.md"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(stderr, "")
        self.assertTrue(stdout.startswith("Generated Markdown: "))
        self.assertEqual(len(markdown_files), 1)

    def test_import_url_error_path_is_unchanged(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            exit_code, stdout, stderr = _run_cli(
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
        self.assertEqual(stdout, "")
        self.assertEqual(
            stderr,
            "Error: yt-dlp metadata provider currently supports YouTube only.\n",
        )


if __name__ == "__main__":
    unittest.main()
