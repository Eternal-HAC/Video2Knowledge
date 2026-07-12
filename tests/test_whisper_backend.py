from __future__ import annotations

import builtins
import sys
import tempfile
import traceback
import types
import unittest
from pathlib import Path
from unittest import mock

from app.audio import NormalizedAudio
from app.errors import LocalTranscriptionError
from app.whisper import (
    FASTER_WHISPER_PROVIDER_ID,
    FasterWhisperBackend,
    LOCAL_WHISPER_MOCK_PROVIDER_ID,
    MockWhisperBackend,
    _format_timestamp,
)
from app.downloader import get_mock_metadata


_REAL_IMPORT = builtins.__import__


class FasterWhisperBackendTests(unittest.TestCase):
    def test_constructor_has_no_dependency_file_or_model_side_effects(self) -> None:
        real_import = builtins.__import__

        def reject_faster_whisper(name, *args, **kwargs):
            if name == "faster_whisper":
                raise AssertionError("constructor imported faster-whisper")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=reject_faster_whisper):
            backend = FasterWhisperBackend(
                model_size="tiny",
                device="cpu",
                compute_type="int8",
                language="en",
            )

        self.assertEqual(backend.model_size, "tiny")
        self.assertEqual(backend.device, "cpu")
        self.assertEqual(backend.compute_type, "int8")
        self.assertEqual(backend.language, "en")

    def test_missing_input_is_rejected_before_dependency_import(self) -> None:
        audio = _normalized_audio(Path("private-missing-input.wav"))
        real_import = builtins.__import__

        def reject_faster_whisper(name, *args, **kwargs):
            if name == "faster_whisper":
                raise AssertionError("missing input imported faster-whisper")
            return real_import(name, *args, **kwargs)

        with mock.patch("builtins.__import__", side_effect=reject_faster_whisper):
            with self.assertRaises(LocalTranscriptionError) as context:
                FasterWhisperBackend().transcribe(audio)

        self.assertEqual(
            str(context.exception),
            "normalized audio input file not found",
        )
        self.assertNotIn("private-missing-input.wav", str(context.exception))

    def test_missing_dependency_returns_stable_error(self) -> None:
        with _temporary_audio() as audio:
            with mock.patch(
                "builtins.__import__",
                side_effect=_failing_faster_whisper_import(
                    ImportError("C:\\private\\dependency.py token=secret")
                ),
            ):
                with self.assertRaises(LocalTranscriptionError) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(str(context.exception), "faster-whisper is not installed")
        _assert_sanitized_traceback(self, context.exception)

    def test_dependency_initialization_failure_is_sanitized(self) -> None:
        with _temporary_audio() as audio:
            with mock.patch(
                "builtins.__import__",
                side_effect=_failing_faster_whisper_import(
                    OSError(
                        "C:\\Users\\private\\.cache\\model.dll token=secret"
                    )
                ),
            ):
                with self.assertRaises(LocalTranscriptionError) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(str(context.exception), "local transcription failed")
        _assert_sanitized_traceback(self, context.exception)

    def test_model_and_transcribe_receive_expected_arguments(self) -> None:
        fake_module, model = _fake_faster_whisper_module(
            [_segment(0.0, 1.25, " hello ")],
            language="en",
        )
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                result = FasterWhisperBackend(
                    model_size="medium",
                    device="cuda",
                    compute_type="float16",
                    language="zh",
                ).transcribe(audio)
                input_path = str(audio.path)

        fake_module.WhisperModel.assert_called_once_with(
            "medium",
            device="cuda",
            compute_type="float16",
        )
        model.transcribe.assert_called_once_with(input_path, language="zh")
        self.assertEqual(result.provider, FASTER_WHISPER_PROVIDER_ID)
        self.assertEqual(result.attempted_providers, [FASTER_WHISPER_PROVIDER_ID])

    def test_single_segment_is_mapped(self) -> None:
        fake_module, _ = _fake_faster_whisper_module(
            [_segment(1.5, 65.25, " First segment. ")]
        )
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                result = FasterWhisperBackend().transcribe(audio)

        self.assertEqual(len(result.segments), 1)
        self.assertEqual(result.segments[0].start, "00:00:01.500")
        self.assertEqual(result.segments[0].end, "00:01:05.250")
        self.assertEqual(result.segments[0].text, "First segment.")

    def test_multiple_segments_preserve_order_time_and_text(self) -> None:
        fake_module, _ = _fake_faster_whisper_module(
            [
                _segment(0.0, 2.0, "one"),
                _segment(2.0, 3.75, "two"),
                _segment(3.75, 4.0, "three"),
            ]
        )
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                result = FasterWhisperBackend().transcribe(audio)

        self.assertEqual(
            [(item.start, item.end, item.text) for item in result.segments],
            [
                ("00:00:00.000", "00:00:02.000", "one"),
                ("00:00:02.000", "00:00:03.750", "two"),
                ("00:00:03.750", "00:00:04.000", "three"),
            ],
        )

    def test_empty_result_returns_stable_error(self) -> None:
        fake_module, _ = _fake_faster_whisper_module([])
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                with self.assertRaises(LocalTranscriptionError) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(
            str(context.exception),
            "local transcription produced no segments",
        )

    def test_model_construction_failure_is_sanitized(self) -> None:
        fake_module = types.ModuleType("faster_whisper")
        fake_module.WhisperModel = mock.Mock(
            side_effect=RuntimeError("private-model-cache token=secret")
        )
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                with self.assertRaises(LocalTranscriptionError) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(str(context.exception), "local transcription failed")
        _assert_sanitized_traceback(self, context.exception)

    def test_transcribe_immediate_failure_is_sanitized(self) -> None:
        fake_module, model = _fake_faster_whisper_module([])
        model.transcribe.side_effect = RuntimeError(
            "C:\\private\\audio.wav?token=secret credential=hidden"
        )
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                with self.assertRaises(LocalTranscriptionError) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(str(context.exception), "local transcription failed")
        _assert_sanitized_traceback(self, context.exception)

    def test_segment_iteration_failure_is_sanitized(self) -> None:
        def failing_segments():
            yield _segment(0.0, 1.0, "first")
            raise RuntimeError("private-input-path token=secret")

        fake_module, _ = _fake_faster_whisper_module(failing_segments())
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                with self.assertRaises(LocalTranscriptionError) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(str(context.exception), "local transcription failed")
        _assert_sanitized_traceback(self, context.exception)

    def test_segment_field_failure_is_sanitized(self) -> None:
        class FailingSegment:
            @property
            def text(self):
                raise RuntimeError("C:\\private\\segment token=secret")

        fake_module, _ = _fake_faster_whisper_module([FailingSegment()])
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                with self.assertRaises(LocalTranscriptionError) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(str(context.exception), "local transcription failed")
        _assert_sanitized_traceback(self, context.exception)

    def test_timestamp_conversion_failure_is_sanitized(self) -> None:
        class FailingTimestamp:
            def __float__(self):
                raise ValueError("C:\\private\\timestamp token=secret")

        fake_module, _ = _fake_faster_whisper_module(
            [_segment(FailingTimestamp(), 1.0, "text")]
        )
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                with self.assertRaises(LocalTranscriptionError) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(str(context.exception), "local transcription failed")
        _assert_sanitized_traceback(self, context.exception)

    def test_non_normalized_audio_is_rejected_before_dependency_import(self) -> None:
        with mock.patch(
            "builtins.__import__",
            side_effect=_reject_faster_whisper_import,
        ):
            with self.assertRaises(LocalTranscriptionError) as context:
                FasterWhisperBackend().transcribe(object())

        self.assertEqual(str(context.exception), "normalized audio input required")

    def test_directory_input_is_rejected_before_dependency_import(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            audio = _normalized_audio(Path(temp_dir))
            with mock.patch(
                "builtins.__import__",
                side_effect=_reject_faster_whisper_import,
            ):
                with self.assertRaises(LocalTranscriptionError) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(
            str(context.exception),
            "normalized audio input must be a file",
        )

    def test_import_keyboard_interrupt_propagates(self) -> None:
        with _temporary_audio() as audio:
            with mock.patch(
                "builtins.__import__",
                side_effect=_failing_faster_whisper_import(KeyboardInterrupt()),
            ):
                with self.assertRaises(KeyboardInterrupt):
                    FasterWhisperBackend().transcribe(audio)

    def test_model_system_exit_propagates(self) -> None:
        fake_module = types.ModuleType("faster_whisper")
        fake_module.WhisperModel = mock.Mock(side_effect=SystemExit(7))
        with _temporary_audio() as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                with self.assertRaises(SystemExit) as context:
                    FasterWhisperBackend().transcribe(audio)

        self.assertEqual(context.exception.code, 7)

    def test_timestamp_boundaries(self) -> None:
        cases = [
            (0.0, "00:00:00.000"),
            (1.234, "00:00:01.234"),
            (3661.25, "01:01:01.250"),
            (59.9996, "00:01:00.000"),
            (3599.9996, "01:00:00.000"),
            (1.2346, "00:00:01.235"),
        ]

        for value, expected in cases:
            with self.subTest(value=value):
                self.assertEqual(_format_timestamp(value), expected)

    def test_non_finite_and_negative_timestamps_return_stable_error(self) -> None:
        for value in (-0.001, float("nan"), float("inf"), float("-inf")):
            with self.subTest(value=value):
                fake_module, _ = _fake_faster_whisper_module(
                    [_segment(value, 1.0, "text")]
                )
                with _temporary_audio() as audio:
                    with mock.patch.dict(
                        sys.modules,
                        {"faster_whisper": fake_module},
                    ):
                        with self.assertRaises(LocalTranscriptionError) as context:
                            FasterWhisperBackend().transcribe(audio)

                self.assertEqual(
                    str(context.exception),
                    "local transcription failed",
                )
                _assert_sanitized_traceback(self, context.exception)

    def test_input_audio_is_not_modified_or_deleted(self) -> None:
        fake_module, _ = _fake_faster_whisper_module(
            [_segment(0.0, 1.0, "unchanged")]
        )
        with _temporary_audio(content=b"original audio") as audio:
            with mock.patch.dict(sys.modules, {"faster_whisper": fake_module}):
                FasterWhisperBackend().transcribe(audio)
            self.assertTrue(audio.path.exists())
            self.assertEqual(audio.path.read_bytes(), b"original audio")

    def test_mock_backend_behavior_does_not_regress(self) -> None:
        metadata = get_mock_metadata("https://example.com/watch?v=mock")

        result = MockWhisperBackend().transcribe(metadata)

        self.assertEqual(result.provider, LOCAL_WHISPER_MOCK_PROVIDER_ID)
        self.assertEqual(result.attempted_providers, [LOCAL_WHISPER_MOCK_PROVIDER_ID])
        self.assertEqual(len(result.segments), 3)
        self.assertEqual(result.segments[0].start, "00:00:00")


def _segment(start: float, end: float, text: str) -> object:
    return types.SimpleNamespace(start=start, end=end, text=text)


def _reject_faster_whisper_import(name, *args, **kwargs):
    if name == "faster_whisper":
        raise AssertionError("faster-whisper import must not occur")
    return _REAL_IMPORT(name, *args, **kwargs)


def _failing_faster_whisper_import(error: BaseException):
    def import_with_failure(name, *args, **kwargs):
        if name == "faster_whisper":
            raise error
        return _REAL_IMPORT(name, *args, **kwargs)

    return import_with_failure


def _assert_sanitized_traceback(
    test_case: unittest.TestCase,
    error: LocalTranscriptionError,
) -> None:
    formatted = "".join(
        traceback.format_exception(type(error), error, error.__traceback__)
    )
    test_case.assertIsNone(error.__cause__)
    test_case.assertTrue(error.__suppress_context__)
    test_case.assertNotIn("C:\\private", formatted)
    test_case.assertNotIn("C:\\Users\\private", formatted)
    test_case.assertNotIn("model.dll", formatted)
    test_case.assertNotIn("token=secret", formatted)
    test_case.assertNotIn("credential=hidden", formatted)
    test_case.assertNotIn("private-model-cache", formatted)
    test_case.assertNotIn("private-input-path", formatted)
    test_case.assertNotIn("private dependency", formatted)


def _fake_faster_whisper_module(
    segments: object,
    language: str = "en",
) -> tuple[types.ModuleType, mock.Mock]:
    module = types.ModuleType("faster_whisper")
    model = mock.Mock()
    model.transcribe.return_value = (
        segments,
        types.SimpleNamespace(language=language),
    )
    module.WhisperModel = mock.Mock(return_value=model)
    return module, model


class _temporary_audio:
    def __init__(self, content: bytes = b"fake normalized audio") -> None:
        self.content = content
        self._temp_dir: tempfile.TemporaryDirectory[str] | None = None

    def __enter__(self) -> NormalizedAudio:
        self._temp_dir = tempfile.TemporaryDirectory()
        path = Path(self._temp_dir.name) / "normalized.wav"
        path.write_bytes(self.content)
        return _normalized_audio(path)

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self._temp_dir is not None:
            self._temp_dir.cleanup()


def _normalized_audio(path: Path) -> NormalizedAudio:
    return NormalizedAudio(
        path=path,
        provider="test_normalizer",
        format="wav",
        sample_rate=16000,
        channels=1,
        temporary=True,
    )


if __name__ == "__main__":
    unittest.main()
