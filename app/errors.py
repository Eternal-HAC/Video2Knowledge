"""Project-specific exceptions."""

from __future__ import annotations


class ProviderNotImplementedError(NotImplementedError):
    """Raised when a non-Mock provider boundary exists but is not implemented yet."""


class MetadataProviderError(RuntimeError):
    """Raised when a metadata provider cannot return a valid metadata result."""


class TranscriptProviderError(RuntimeError):
    """Raised when a transcript provider cannot return a valid transcript result."""
