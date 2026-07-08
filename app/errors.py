"""Project-specific exceptions."""

from __future__ import annotations


class ProviderNotImplementedError(NotImplementedError):
    """Raised when a non-Mock provider boundary exists but is not implemented yet."""


class MetadataProviderError(RuntimeError):
    """Raised when a metadata provider cannot return a valid metadata result."""


class TranscriptProviderError(RuntimeError):
    """Raised when a transcript provider cannot return a valid transcript result."""


class NoOfficialSubtitleError(TranscriptProviderError):
    """Raised when a source has no official subtitles available."""


class UnsupportedSubtitleFormatError(TranscriptProviderError):
    """Raised when official subtitles exist but no supported format is available."""


class PlatformAccessError(TranscriptProviderError):
    """Raised when the platform refuses or restricts transcript access."""


class NetworkAccessError(TranscriptProviderError):
    """Raised when transcript access fails because of network conditions."""
