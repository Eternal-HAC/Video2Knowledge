from __future__ import annotations

import contextlib
import hashlib
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from app.audio import (
    AudioArtifact,
    AudioProcessingError,
    AudioWorkspace,
    FfmpegAudioNormalizer,
    NormalizedAudio,
    _remove_failed_normalized_output,
)
from app.downloader import get_mock_metadata
from app.errors import AudioAcquisitionError, LocalTranscriptionError
from app.models import TranscriptResult, TranscriptSegment
from app.pipeline import transcribe_local_media


class LocalAsrOrchestrationTests(unittest.TestCase):
    def test_success_preserves_order_contract_and_user_file(self) -> None:
        events: list[str] = []
        state: dict[str, object] = {}
        result = _transcript_result()

        with tempfile.TemporaryDirectory() as temp_dir:
            original_path = Path(temp_dir) / "user-input.m4a"
            original_path.write_bytes(b"user-owned audio")
            original_hash = _hash_file(original_path)
            metadata = get_mock_metadata(str(original_path), platform="local")
            provider = _Provider(original_path, events)
            backend = _Backend(result, events, state)

            original_register = AudioWorkspace.register

            def register(workspace, artifact):
                events.append("register")
                state["registered"] = True
                return original_register(workspace, artifact)

            with mock.patch.object(AudioWorkspace, "register", new=register):
                returned = transcribe_local_media(
                    metadata,
                    whisper_backend=backend,
                    audio_provider=provider,
                    normalizer_factory=_normalizer_factory(events, state),
                )

            normalized_path = state["normalized_path"]
            workspace_path = state["workspace_path"]

            self.assertIs(returned, result)
            self.assertEqual(events, ["provider", "factory", "normalizer", "register", "whisper"])
            self.assertIs(provider.metadata, metadata)
            self.assertFalse(provider.artifact.temporary)
            self.assertIs(state["normalizer_artifact"], provider.artifact)
            self.assertTrue(state["whisper_saw_registered"])
            self.assertIs(state["whisper_audio"], state["normalized"])
            self.assertFalse(normalized_path.exists())
            self.assertFalse(workspace_path.exists())
            self.assertTrue(original_path.exists())
            self.assertEqual(original_path.read_bytes(), b"user-owned audio")
            self.assertEqual(_hash_file(original_path), original_hash)
            self.assertEqual(returned.provider, "faster_whisper")
            self.assertEqual(returned.attempted_providers, ["faster_whisper"])

    def test_provider_failure_stops_before_workspace_and_downstream(self) -> None:
        metadata = get_mock_metadata("missing.wav", platform="local")
        provider = mock.Mock()
        provider.acquire.side_effect = AudioAcquisitionError("local audio input file not found")
        factory = mock.Mock()
        backend = mock.Mock()

        with mock.patch("app.pipeline.AudioWorkspace") as workspace:
            with self.assertRaises(AudioAcquisitionError):
                transcribe_local_media(
                    metadata,
                    whisper_backend=backend,
                    audio_provider=provider,
                    normalizer_factory=factory,
                )

        workspace.assert_not_called()
        factory.assert_not_called()
        backend.transcribe.assert_not_called()

    def test_non_local_metadata_fails_before_provider_or_workspace(self) -> None:
        metadata = get_mock_metadata(
            "https://example.com/watch?v=private-token",
            platform="youtube",
        )
        provider = mock.Mock()
        factory = mock.Mock()
        backend = mock.Mock()

        with mock.patch("app.pipeline.AudioWorkspace") as workspace:
            with self.assertRaises(AudioAcquisitionError) as context:
                transcribe_local_media(
                    metadata,
                    whisper_backend=backend,
                    audio_provider=provider,
                    normalizer_factory=factory,
                )

        self.assertEqual(str(context.exception), "local audio input required")
        self.assertNotIn(metadata.source_url, str(context.exception))
        provider.acquire.assert_not_called()
        workspace.assert_not_called()
        factory.assert_not_called()
        backend.transcribe.assert_not_called()

    def test_temporary_provider_artifact_is_rejected_without_deletion(self) -> None:
        with _local_input() as (metadata, original_path):
            temporary_path = original_path.parent / "downloaded-temporary.m4a"
            temporary_path.write_bytes(b"temporary provider output")
            provider = mock.Mock()
            provider.acquire.return_value = AudioArtifact(
                path=temporary_path,
                provider="yt_dlp_audio",
                format="m4a",
                temporary=True,
            )
            factory = mock.Mock()
            backend = mock.Mock()

            with mock.patch("app.pipeline.AudioWorkspace") as workspace:
                with self.assertRaises(AudioAcquisitionError) as context:
                    transcribe_local_media(
                        metadata,
                        whisper_backend=backend,
                        audio_provider=provider,
                        normalizer_factory=factory,
                    )

            self.assertEqual(
                str(context.exception),
                "local audio input must be user-owned",
            )
            self.assertTrue(temporary_path.exists())
            self.assertEqual(
                temporary_path.read_bytes(),
                b"temporary provider output",
            )
            workspace.assert_not_called()
            factory.assert_not_called()
            backend.transcribe.assert_not_called()

    def test_provider_directory_and_missing_artifacts_are_rejected(self) -> None:
        with _local_input() as (metadata, original_path):
            cases = [
                (original_path.parent, "local audio input must be a file"),
                (
                    original_path.parent / "missing-provider-output.wav",
                    "local audio input file not found",
                ),
            ]
            for path, expected in cases:
                with self.subTest(path=path.name):
                    provider = mock.Mock()
                    provider.acquire.return_value = _audio_artifact(path)
                    factory = mock.Mock()
                    backend = mock.Mock()
                    with mock.patch("app.pipeline.AudioWorkspace") as workspace:
                        with self.assertRaises(AudioAcquisitionError) as context:
                            transcribe_local_media(
                                metadata,
                                whisper_backend=backend,
                                audio_provider=provider,
                                normalizer_factory=factory,
                            )

                    self.assertEqual(str(context.exception), expected)
                    workspace.assert_not_called()
                    factory.assert_not_called()
                    backend.transcribe.assert_not_called()

    def test_provider_symlink_semantics_are_rejected_before_workspace(self) -> None:
        with _local_input() as (metadata, original_path):
            provider = mock.Mock()
            provider.acquire.return_value = _audio_artifact(original_path)
            with mock.patch.object(Path, "is_symlink", return_value=True):
                with mock.patch("app.pipeline.AudioWorkspace") as workspace:
                    with self.assertRaises(AudioAcquisitionError) as context:
                        transcribe_local_media(
                            metadata,
                            whisper_backend=mock.Mock(),
                            audio_provider=provider,
                            normalizer_factory=mock.Mock(),
                        )

            self.assertEqual(
                str(context.exception),
                "local audio input must be a file",
            )
            workspace.assert_not_called()

    def test_normalizer_failure_stops_before_whisper(self) -> None:
        with _local_input() as (metadata, original_path):
            provider = _Provider(original_path, [])
            normalizer = mock.Mock()
            normalizer.normalize.side_effect = AudioProcessingError("ffmpeg audio normalization failed")
            backend = mock.Mock()

            with self.assertRaises(AudioProcessingError):
                transcribe_local_media(
                    metadata,
                    whisper_backend=backend,
                    audio_provider=provider,
                    normalizer_factory=lambda _: normalizer,
                )

        normalizer.normalize.assert_called_once_with(provider.artifact)
        backend.transcribe.assert_not_called()

    def test_whisper_failure_cleans_registered_output(self) -> None:
        state: dict[str, object] = {}
        with _local_input() as (metadata, original_path):
            backend = _Backend(
                _transcript_result(),
                [],
                state,
                error=LocalTranscriptionError("local transcription failed"),
            )
            with self.assertRaises(LocalTranscriptionError):
                transcribe_local_media(
                    metadata,
                    whisper_backend=backend,
                    audio_provider=_Provider(original_path, []),
                    normalizer_factory=_normalizer_factory([], state),
                )

            self.assertFalse(state["normalized_path"].exists())
            self.assertFalse(state["workspace_path"].exists())
            self.assertTrue(original_path.exists())

    def test_registration_failure_stops_before_whisper(self) -> None:
        state: dict[str, object] = {}
        with _local_input() as (metadata, original_path):
            backend = mock.Mock()
            with mock.patch.object(
                AudioWorkspace,
                "register",
                side_effect=AudioProcessingError("registration failed"),
            ):
                with self.assertRaisesRegex(AudioProcessingError, "registration failed"):
                    transcribe_local_media(
                        metadata,
                        whisper_backend=backend,
                        audio_provider=_Provider(original_path, []),
                        normalizer_factory=_normalizer_factory([], state),
                    )

            backend.transcribe.assert_not_called()
            self.assertFalse(state["normalized_path"].exists())
            self.assertFalse(state["workspace_path"].exists())

    def test_registration_rejection_cleans_exact_inside_outputs(self) -> None:
        for case in ("non_temporary", "directory", "missing"):
            with self.subTest(case=case):
                state: dict[str, object] = {}
                with _local_input() as (metadata, original_path):
                    backend = mock.Mock()
                    with self.assertRaises(AudioProcessingError):
                        transcribe_local_media(
                            metadata,
                            whisper_backend=backend,
                            audio_provider=_Provider(original_path, []),
                            normalizer_factory=_invalid_normalizer_factory(case, state),
                        )

                    backend.transcribe.assert_not_called()
                    self.assertFalse(state["invalid_path"].exists())
                    self.assertFalse(state["workspace_path"].exists())

    def test_registration_rejection_preserves_workspace_external_output(self) -> None:
        state: dict[str, object] = {}
        with _local_input() as (metadata, original_path):
            backend = mock.Mock()
            with self.assertRaises(AudioProcessingError):
                transcribe_local_media(
                    metadata,
                    whisper_backend=backend,
                    audio_provider=_Provider(original_path, []),
                    normalizer_factory=_invalid_normalizer_factory("outside", state),
                )

            self.assertTrue(state["invalid_path"].exists())
            self.assertEqual(state["invalid_path"].read_bytes(), b"outside")
            self.assertFalse(state["workspace_path"].exists())
            backend.transcribe.assert_not_called()
            state["invalid_path"].unlink()

    def test_non_empty_directory_is_not_recursively_deleted(self) -> None:
        state: dict[str, object] = {}
        with _local_input() as (metadata, original_path):
            backend = mock.Mock()
            with self.assertRaises(AudioProcessingError) as context:
                transcribe_local_media(
                    metadata,
                    whisper_backend=backend,
                    audio_provider=_Provider(original_path, []),
                    normalizer_factory=_invalid_normalizer_factory(
                        "non_empty_directory",
                        state,
                    ),
                )

            self.assertEqual(
                str(context.exception),
                "audio workspace artifact must be a file",
            )
            self.assertTrue(state["invalid_path"].is_dir())
            self.assertTrue(state["unknown_path"].exists())
            self.assertTrue(state["workspace_path"].exists())
            backend.transcribe.assert_not_called()
            _cleanup_test_workspace(state)

    def test_symlink_escape_is_rejected_without_deleting_external_target(self) -> None:
        state: dict[str, object] = {}
        with _local_input() as (metadata, original_path):
            external_target = original_path.parent / "external-target.wav"
            external_target.write_bytes(b"external target")

            def factory(workspace_path: Path):
                state["workspace_path"] = workspace_path
                link_path = workspace_path / "normalized-link.wav"
                try:
                    link_path.symlink_to(external_target)
                except OSError as error:
                    self.skipTest(f"symlink creation unavailable: {error}")
                state["invalid_path"] = link_path
                return mock.Mock(
                    normalize=mock.Mock(return_value=_normalized_audio(link_path))
                )

            with self.assertRaises(AudioProcessingError):
                transcribe_local_media(
                    metadata,
                    whisper_backend=mock.Mock(),
                    audio_provider=_Provider(original_path, []),
                    normalizer_factory=factory,
                )

            self.assertTrue(external_target.exists())
            self.assertEqual(external_target.read_bytes(), b"external target")
            self.assertTrue(state["invalid_path"].is_symlink())
            self.assertTrue(state["workspace_path"].exists())
            state["invalid_path"].unlink()
            state["workspace_path"].rmdir()

    def test_cleanup_failure_without_business_error_is_reported(self) -> None:
        state: dict[str, object] = {"create_unknown": True}
        with _local_input() as (metadata, original_path):
            with self.assertRaisesRegex(AudioProcessingError, "audio workspace cleanup failed"):
                transcribe_local_media(
                    metadata,
                    whisper_backend=_Backend(_transcript_result(), [], state),
                    audio_provider=_Provider(original_path, []),
                    normalizer_factory=_normalizer_factory([], state),
                )

        _cleanup_test_workspace(state)

    def test_cleanup_failure_does_not_mask_business_error(self) -> None:
        state: dict[str, object] = {"create_unknown": True}
        error = LocalTranscriptionError("local transcription failed")
        with _local_input() as (metadata, original_path):
            with self.assertRaises(LocalTranscriptionError) as context:
                transcribe_local_media(
                    metadata,
                    whisper_backend=_Backend(
                        _transcript_result(), [], state, error=error
                    ),
                    audio_provider=_Provider(original_path, []),
                    normalizer_factory=_normalizer_factory([], state),
                )

        self.assertIs(context.exception, error)
        _cleanup_test_workspace(state)

    def test_user_file_hash_is_preserved_across_outcome_matrix(self) -> None:
        scenarios = (
            "success",
            "normalizer_failure",
            "registration_failure",
            "whisper_failure",
            "keyboard_interrupt",
            "system_exit",
            "cleanup_failure",
            "business_and_cleanup_failure",
        )
        for scenario in scenarios:
            with self.subTest(scenario=scenario):
                state: dict[str, object] = {}
                if scenario in ("cleanup_failure", "business_and_cleanup_failure"):
                    state["create_unknown"] = True

                with _local_input() as (metadata, original_path):
                    original_hash = _hash_file(original_path)
                    provider = _Provider(original_path, [])
                    backend_error: BaseException | None = None
                    if scenario in ("whisper_failure", "business_and_cleanup_failure"):
                        backend_error = LocalTranscriptionError(
                            "local transcription failed"
                        )
                    elif scenario == "keyboard_interrupt":
                        backend_error = KeyboardInterrupt()
                    elif scenario == "system_exit":
                        backend_error = SystemExit(7)

                    backend = _Backend(
                        _transcript_result(),
                        [],
                        state,
                        error=backend_error,
                    )
                    factory = _normalizer_factory([], state)

                    if scenario == "normalizer_failure":
                        normalizer = mock.Mock()
                        normalizer.normalize.side_effect = AudioProcessingError(
                            "ffmpeg audio normalization failed"
                        )
                        factory = lambda _: normalizer

                    expected_error: type[BaseException] | None = None
                    if scenario in (
                        "normalizer_failure",
                        "registration_failure",
                        "cleanup_failure",
                    ):
                        expected_error = AudioProcessingError
                    elif scenario in (
                        "whisper_failure",
                        "business_and_cleanup_failure",
                    ):
                        expected_error = LocalTranscriptionError
                    elif scenario == "keyboard_interrupt":
                        expected_error = KeyboardInterrupt
                    elif scenario == "system_exit":
                        expected_error = SystemExit

                    registration_patch = (
                        mock.patch.object(
                            AudioWorkspace,
                            "register",
                            side_effect=AudioProcessingError("registration failed"),
                        )
                        if scenario == "registration_failure"
                        else contextlib.nullcontext()
                    )

                    with registration_patch:
                        if expected_error is None:
                            transcribe_local_media(
                                metadata,
                                whisper_backend=backend,
                                audio_provider=provider,
                                normalizer_factory=factory,
                            )
                        else:
                            with self.assertRaises(expected_error):
                                transcribe_local_media(
                                    metadata,
                                    whisper_backend=backend,
                                    audio_provider=provider,
                                    normalizer_factory=factory,
                                )

                    _assert_user_file_unchanged(
                        self,
                        original_path,
                        original_hash,
                    )
                    _cleanup_test_workspace(state)

    def test_control_flow_exceptions_propagate_after_cleanup(self) -> None:
        for error in (KeyboardInterrupt(), SystemExit(7)):
            with self.subTest(error=type(error).__name__):
                state: dict[str, object] = {}
                with _local_input() as (metadata, original_path):
                    with self.assertRaises(type(error)):
                        transcribe_local_media(
                            metadata,
                            whisper_backend=_Backend(
                                _transcript_result(), [], state, error=error
                            ),
                            audio_provider=_Provider(original_path, []),
                            normalizer_factory=_normalizer_factory([], state),
                        )

                    self.assertFalse(state["normalized_path"].exists())
                    self.assertFalse(state["workspace_path"].exists())
                    self.assertTrue(original_path.exists())

    def test_control_flow_exceptions_survive_cleanup_failure(self) -> None:
        for error in (KeyboardInterrupt(), SystemExit(7)):
            with self.subTest(error=type(error).__name__):
                state: dict[str, object] = {}
                with _local_input() as (metadata, original_path):
                    original_hash = _hash_file(original_path)
                    cleanup_error = AudioProcessingError(
                        "audio workspace cleanup failed"
                    )
                    with mock.patch.object(
                        AudioWorkspace,
                        "cleanup",
                        side_effect=cleanup_error,
                    ) as cleanup:
                        with self.assertRaises(type(error)) as context:
                            transcribe_local_media(
                                metadata,
                                whisper_backend=_Backend(
                                    _transcript_result(),
                                    [],
                                    state,
                                    error=error,
                                ),
                                audio_provider=_Provider(original_path, []),
                                normalizer_factory=_normalizer_factory([], state),
                            )

                    cleanup.assert_called_once_with()
                    self.assertIs(context.exception, error)
                    if isinstance(error, SystemExit):
                        self.assertEqual(context.exception.code, 7)
                    _assert_user_file_unchanged(
                        self,
                        original_path,
                        original_hash,
                    )
                    _cleanup_test_workspace(state)

    def test_default_normalizer_is_constructed_for_workspace_without_running_ffmpeg(self) -> None:
        with _local_input() as (metadata, original_path):
            provider = _Provider(original_path, [])
            backend = mock.Mock()
            marker = AudioProcessingError("stop before ffmpeg")
            with mock.patch("app.pipeline.FfmpegAudioNormalizer") as normalizer_class:
                normalizer_class.return_value.normalize.side_effect = marker
                with self.assertRaises(AudioProcessingError) as context:
                    transcribe_local_media(
                        metadata,
                        whisper_backend=backend,
                        audio_provider=provider,
                    )

        self.assertIs(context.exception, marker)
        output_dir = normalizer_class.call_args.kwargs["output_dir"]
        self.assertIsInstance(output_dir, Path)
        normalizer_class.return_value.normalize.assert_called_once_with(provider.artifact)
        backend.transcribe.assert_not_called()


class FfmpegFailedOutputCleanupTests(unittest.TestCase):
    def test_timeout_removes_partial_output_and_preserves_input(self) -> None:
        self._assert_failure_removes_partial("timeout")

    def test_non_zero_exit_removes_partial_output_and_preserves_input(self) -> None:
        self._assert_failure_removes_partial("non_zero")

    def test_startup_oserror_removes_partial_output_and_preserves_input(self) -> None:
        self._assert_failure_removes_partial("oserror")

    def _assert_failure_removes_partial(self, failure: str) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "input.m4a"
            output_path = root / "input-16k-mono.wav"
            input_path.write_bytes(b"original")
            artifact = _audio_artifact(input_path)

            def run(command, **kwargs):
                output_path.write_bytes(b"partial")
                if failure == "timeout":
                    raise subprocess.TimeoutExpired(command, 1)
                if failure == "oserror":
                    raise OSError("private path")
                return subprocess.CompletedProcess(command, 1, "", "private stderr")

            with mock.patch("app.audio.subprocess.run", side_effect=run):
                with self.assertRaises(AudioProcessingError) as context:
                    FfmpegAudioNormalizer(
                        output_dir=root,
                        ffmpeg_path="ffmpeg",
                    ).normalize(artifact)

            expected = (
                "ffmpeg audio normalization timed out"
                if failure == "timeout"
                else "ffmpeg audio normalization failed"
            )
            self.assertEqual(str(context.exception), expected)
            self.assertFalse(output_path.exists())
            self.assertTrue(input_path.exists())
            self.assertEqual(input_path.read_bytes(), b"original")

    def test_partial_output_cleanup_failure_does_not_replace_original_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "input.m4a"
            output_path = root / "input-16k-mono.wav"
            input_path.write_bytes(b"original")

            def run(command, **kwargs):
                output_path.write_bytes(b"partial")
                return subprocess.CompletedProcess(command, 1, "", "private stderr")

            original_unlink = Path.unlink

            def fail_output_unlink(path, *args, **kwargs):
                if path == output_path:
                    raise OSError("cleanup failed")
                return original_unlink(path, *args, **kwargs)

            with mock.patch("app.audio.subprocess.run", side_effect=run):
                with mock.patch.object(Path, "unlink", new=fail_output_unlink):
                    with self.assertRaises(AudioProcessingError) as context:
                        FfmpegAudioNormalizer(
                            output_dir=root,
                            ffmpeg_path="ffmpeg",
                        ).normalize(_audio_artifact(input_path))

            self.assertEqual(str(context.exception), "ffmpeg audio normalization failed")
            self.assertTrue(output_path.exists())
            self.assertTrue(input_path.exists())

    def test_existing_output_is_never_deleted(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            input_path = root / "input.m4a"
            output_path = root / "input-16k-mono.wav"
            input_path.write_bytes(b"original")
            output_path.write_bytes(b"existing")

            with mock.patch("app.audio.subprocess.run") as run:
                with self.assertRaisesRegex(
                    AudioProcessingError, "ffmpeg normalized output already exists"
                ):
                    FfmpegAudioNormalizer(
                        output_dir=root,
                        ffmpeg_path="ffmpeg",
                    ).normalize(_audio_artifact(input_path))

            run.assert_not_called()
            self.assertEqual(output_path.read_bytes(), b"existing")
            self.assertEqual(input_path.read_bytes(), b"original")

    def test_cleanup_helper_never_deletes_outside_output_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            output_dir = root / "output"
            output_dir.mkdir()
            outside = root / "outside.wav"
            outside.write_bytes(b"outside")

            _remove_failed_normalized_output(outside, output_dir)

            self.assertTrue(outside.exists())
            self.assertEqual(outside.read_bytes(), b"outside")


class _Provider:
    def __init__(self, path: Path, events: list[str]) -> None:
        self.events = events
        self.metadata = None
        self.artifact = _audio_artifact(path)

    def acquire(self, metadata):
        self.events.append("provider")
        self.metadata = metadata
        return self.artifact


class _Normalizer:
    def __init__(self, workspace_path: Path, events: list[str], state: dict[str, object]) -> None:
        self.workspace_path = workspace_path
        self.events = events
        self.state = state

    def normalize(self, artifact: AudioArtifact) -> NormalizedAudio:
        self.events.append("normalizer")
        self.state["normalizer_artifact"] = artifact
        normalized_path = self.workspace_path / "normalized.wav"
        normalized_path.write_bytes(b"normalized")
        normalized = _normalized_audio(normalized_path)
        self.state["normalized_path"] = normalized_path
        self.state["normalized"] = normalized
        if self.state.get("create_unknown"):
            unknown = self.workspace_path / "unknown.tmp"
            unknown.write_bytes(b"unknown")
            self.state["unknown_path"] = unknown
        return normalized


class _Backend:
    def __init__(
        self,
        result: TranscriptResult,
        events: list[str],
        state: dict[str, object],
        error: BaseException | None = None,
    ) -> None:
        self.result = result
        self.events = events
        self.state = state
        self.error = error

    def transcribe(self, audio: NormalizedAudio) -> TranscriptResult:
        self.events.append("whisper")
        self.state["whisper_audio"] = audio
        self.state["whisper_saw_registered"] = self.state.get("registered", True)
        if self.error is not None:
            raise self.error
        return self.result


def _normalizer_factory(events: list[str], state: dict[str, object]):
    def factory(workspace_path: Path):
        events.append("factory")
        state["workspace_path"] = workspace_path
        return _Normalizer(workspace_path, events, state)

    return factory


def _invalid_normalizer_factory(case: str, state: dict[str, object]):
    def factory(workspace_path: Path):
        state["workspace_path"] = workspace_path
        if case == "outside":
            path = workspace_path.parent / f"outside-{workspace_path.name}.wav"
            path.write_bytes(b"outside")
            artifact = _normalized_audio(path)
        elif case == "non_temporary":
            path = workspace_path / "not-temporary.wav"
            path.write_bytes(b"inside")
            artifact = _normalized_audio(path, temporary=False)
        elif case == "directory":
            path = workspace_path / "directory"
            path.mkdir()
            artifact = _normalized_audio(path)
        elif case == "non_empty_directory":
            path = workspace_path / "directory"
            path.mkdir()
            unknown = path / "unknown.tmp"
            unknown.write_bytes(b"unknown")
            state["unknown_path"] = unknown
            artifact = _normalized_audio(path)
        else:
            path = workspace_path / "missing.wav"
            artifact = _normalized_audio(path)
        state["invalid_path"] = path
        return mock.Mock(normalize=mock.Mock(return_value=artifact))

    return factory


class _local_input:
    def __enter__(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        path = Path(self.temp_dir.name) / "input.m4a"
        path.write_bytes(b"user-owned")
        return get_mock_metadata(str(path), platform="local"), path

    def __exit__(self, exc_type, exc_value, traceback):
        self.temp_dir.cleanup()


def _cleanup_test_workspace(state: dict[str, object]) -> None:
    for key in ("unknown_path", "invalid_path", "normalized_path"):
        path = state.get(key)
        if isinstance(path, Path) and path.exists():
            if path.is_dir():
                path.rmdir()
            else:
                path.unlink()
    workspace_path = state.get("workspace_path")
    if isinstance(workspace_path, Path) and workspace_path.exists():
        workspace_path.rmdir()


def _audio_artifact(path: Path) -> AudioArtifact:
    return AudioArtifact(
        path=path,
        provider="local_file_audio",
        format=path.suffix.lstrip(".") or "unknown",
        temporary=False,
    )


def _normalized_audio(path: Path, temporary: bool = True) -> NormalizedAudio:
    return NormalizedAudio(
        path=path,
        provider="ffmpeg_audio_normalizer",
        format="wav",
        sample_rate=16000,
        channels=1,
        temporary=temporary,
    )


def _transcript_result() -> TranscriptResult:
    return TranscriptResult(
        segments=[TranscriptSegment("00:00:00.000", "00:00:01.000", "text")],
        provider="faster_whisper",
        attempted_providers=["faster_whisper"],
    )


def _hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _assert_user_file_unchanged(
    test_case: unittest.TestCase,
    path: Path,
    expected_hash: str,
) -> None:
    test_case.assertTrue(path.exists())
    test_case.assertTrue(path.is_file())
    test_case.assertEqual(path.read_bytes(), b"user-owned")
    test_case.assertEqual(_hash_file(path), expected_hash)


if __name__ == "__main__":
    unittest.main()
