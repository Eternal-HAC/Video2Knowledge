"""Project-specific exceptions."""

from __future__ import annotations


class ProviderNotImplementedError(NotImplementedError):
    """Raised when a non-Mock provider boundary exists but is not implemented yet."""

