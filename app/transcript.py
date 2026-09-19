"""Transcript provider boundary.

The default provider is Mock. Real subtitle and Whisper providers are explicit
placeholders until external dependencies are introduced.
"""

from __future__ import annotations

import html
import ipaddress
import re
import socket
import string
from typing import Protocol
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urljoin, urlparse, urlunparse
from urllib.request import HTTPRedirectHandler, build_opener

from app.audio import MockAudioNormalizer, MockAudioProvider
from app.errors import (
    NetworkAccessError,
    NoOfficialSubtitleError,
    PlatformAccessError,
    TranscriptProviderError,
    UnsupportedSubtitleFormatError,
)
from app.models import TranscriptResult, TranscriptSegment, VideoMetadata
from app.whisper import LOCAL_WHISPER_MOCK_PROVIDER_ID, MockWhisperBackend


TRANSCRIPT_PROVIDER_ORDER = [
    "official_subtitles",
    "transcript_api",
    "whisper",
]
OFFICIAL_SUBTITLE_PROVIDER_ID = "yt_dlp_official_subtitles"
OFFICIAL_SUBTITLE_LANGUAGE_PRIORITY = ["zh-CN", "zh-Hans", "zh", "en"]
VTT_CUE_SEPARATOR = "-->"

MAX_SUBTITLE_RESPONSE_BYTES = 16 * 1024 * 1024
SUBTITLE_FETCH_TIMEOUT_SECONDS = 30
_UNSAFE_SUBTITLE_URL_MESSAGE = "official subtitle VTT fetch failed: unsafe URL"
_SUBTITLE_TOO_LARGE_MESSAGE = "official subtitle VTT fetch failed: response too large"
_SUBTITLE_ENCODING_MESSAGE = (
    "official subtitle VTT fetch failed: unsupported or invalid subtitle encoding"
)
_LEGACY_NUMERIC_IPV4_PATTERN = re.compile(
    r"^(?:0[xX][0-9a-fA-F]+|[0-9]+)(?:\.(?:0[xX][0-9a-fA-F]+|[0-9]+))*$"
)


class _BoundedRedirectBody:
    """Bound redirect response reads so no unbounded body read can occur.

    The standard library redirect handler drains the redirect response with a
    bare ``fp.read()``; subtitle redirect bodies must obey the same size cap
    as final subtitle responses.
    """

    def __init__(self, body) -> None:
        self._body = body

    def read(self, size: int = -1):
        if size is None or size < 0:
            payload = self._body.read(MAX_SUBTITLE_RESPONSE_BYTES + 1)
            if len(payload) > MAX_SUBTITLE_RESPONSE_BYTES:
                raise TranscriptProviderError(_SUBTITLE_TOO_LARGE_MESSAGE) from None
            return payload
        return self._body.read(size)

    def close(self) -> None:
        # The standard library closes a successfully followed redirect response
        # itself, so this runs twice on that path: cleanup must be best-effort
        # and idempotent rather than a new public failure.
        _close_response_quietly(self._body)

    def __getattr__(self, name):
        return getattr(self._body, name)


class _ValidatingRedirectHandler(HTTPRedirectHandler):
    """Reject unsafe redirect targets and bound/close redirect responses."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Second validation: this is the absolute target the request layer
        # itself computed, checked again right before the next request.
        if not _is_safe_subtitle_url(newurl):
            raise TranscriptProviderError(_UNSAFE_SUBTITLE_URL_MESSAGE) from None
        return super().redirect_request(req, fp, code, msg, headers, newurl)

    def http_error_302(self, req, fp, code, msg, headers):
        bounded_body = _BoundedRedirectBody(fp)
        try:
            raw_location = _redirect_location(headers)
            if raw_location is not None:
                # Checked on the raw value, before ``urlparse``, ``quote`` and
                # ``urljoin`` run: ``urlparse`` removes tab, CR and LF from the
                # whole URL before it splits the authority off, so a check made
                # after parsing would never see those three.
                if not _raw_url_is_usable(raw_location):
                    raise TranscriptProviderError(
                        _UNSAFE_SUBTITLE_URL_MESSAGE
                    ) from None
                # The raw ``Location`` only means something once the request
                # layer has quoted it and resolved it against the request
                # URL, so the effective absolute target is what gets
                # validated -- before the redirect body is read and before
                # ``parent.open`` can run.
                effective_target = _effective_redirect_target(req, raw_location)
                if effective_target is None or not _is_safe_subtitle_url(
                    effective_target
                ):
                    raise TranscriptProviderError(
                        _UNSAFE_SUBTITLE_URL_MESSAGE
                    ) from None
            return super().http_error_302(req, bounded_body, code, msg, headers)
        finally:
            _close_response_quietly(bounded_body)

    http_error_301 = http_error_303 = http_error_307 = http_error_308 = http_error_302


_subtitle_opener = build_opener(_ValidatingRedirectHandler())
urlopen = _subtitle_opener.open


class TranscriptProvider(Protocol):
    """Interface for acquiring transcript segments."""

    name: str

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        """Acquire transcript data for a video."""


class MockTranscriptProvider:
    name = "mock"

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        return acquire_transcript_mock(metadata)


class RealFallbackTranscriptProvider:
    name = "real-fallback"

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        try:
            return YtDlpOfficialSubtitleProvider().acquire(metadata)
        except TranscriptProviderError as error:
            if should_fallback_to_whisper(error):
                audio = MockAudioProvider().acquire(metadata)
                _normalized_audio = MockAudioNormalizer().normalize(audio)
                result = MockWhisperBackend().transcribe(metadata)
                return TranscriptResult(
                    segments=result.segments,
                    provider=LOCAL_WHISPER_MOCK_PROVIDER_ID,
                    attempted_providers=[
                        OFFICIAL_SUBTITLE_PROVIDER_ID,
                        LOCAL_WHISPER_MOCK_PROVIDER_ID,
                    ],
                )
            raise


class YtDlpOfficialSubtitleProvider:
    name = "official-subtitles"

    def acquire(self, metadata: VideoMetadata) -> TranscriptResult:
        if metadata.platform != "youtube":
            raise PlatformAccessError(
                "Official subtitle provider currently supports YouTube only."
            )
        if not isinstance(metadata.raw_metadata, dict):
            raise TranscriptProviderError(
                "Official subtitle provider requires yt-dlp raw metadata."
            )

        subtitles = metadata.raw_metadata.get("subtitles")
        if not isinstance(subtitles, dict) or not subtitles:
            raise NoOfficialSubtitleError(
                "No official subtitles found in yt-dlp metadata. "
                "Automatic captions are not used in this stage."
            )

        track = select_official_vtt_track(subtitles)
        if track is None:
            raise UnsupportedSubtitleFormatError(
                "Official subtitles were found, but no VTT/WebVTT track is supported."
            )

        url = _string_value(track.get("url"))
        if not url:
            raise TranscriptProviderError("Selected official subtitle VTT track has no URL.")

        vtt_text = fetch_text(url)
        segments = parse_vtt_segments(vtt_text)
        if not segments:
            raise TranscriptProviderError("Selected official subtitle VTT track has no cues.")

        return TranscriptResult(
            segments=segments,
            provider=OFFICIAL_SUBTITLE_PROVIDER_ID,
            attempted_providers=[OFFICIAL_SUBTITLE_PROVIDER_ID],
        )


def get_mock_transcript(metadata: VideoMetadata) -> list[TranscriptSegment]:
    """Return deterministic transcript segments for Mock processing."""

    return [
        TranscriptSegment("00:00:00", "00:00:20", f"这是来自 {metadata.platform} 的 Mock 视频内容。"),
        TranscriptSegment("00:00:20", "00:00:45", "Video2Knowledge 会把视频信息转成结构化 Markdown。"),
        TranscriptSegment("00:00:45", "00:01:10", "当前阶段只验证本地流水线，不调用真实 API。"),
    ]


def acquire_transcript_mock(metadata: VideoMetadata) -> TranscriptResult:
    """Return Mock transcript data while preserving the future fallback order."""

    return TranscriptResult(
        segments=get_mock_transcript(metadata),
        provider="mock_official_subtitles",
        attempted_providers=TRANSCRIPT_PROVIDER_ORDER,
    )


def acquire_transcript_with_provider(
    metadata: VideoMetadata,
    provider_name: str = "mock",
) -> TranscriptResult:
    """Acquire transcript data with an explicit provider name."""

    provider = build_transcript_provider(provider_name)
    return provider.acquire(metadata)


def build_transcript_provider(provider_name: str) -> TranscriptProvider:
    """Create a transcript provider by name."""

    normalized = provider_name.lower()
    if normalized == "mock":
        return MockTranscriptProvider()
    if normalized == "official-subtitles":
        return YtDlpOfficialSubtitleProvider()
    if normalized == "real-fallback":
        return RealFallbackTranscriptProvider()
    raise ValueError(f"Unknown transcript provider: {provider_name}")


def should_fallback_to_whisper(error: TranscriptProviderError) -> bool:
    """Return whether a transcript error is eligible for future Whisper fallback."""

    return isinstance(error, (NoOfficialSubtitleError, UnsupportedSubtitleFormatError))


def select_official_vtt_track(
    subtitles: dict[str, object],
) -> dict[str, object] | None:
    """Select the best official VTT/WebVTT subtitle track."""

    for language in OFFICIAL_SUBTITLE_LANGUAGE_PRIORITY:
        track = _first_vtt_track(subtitles.get(language))
        if track is not None:
            return track

    for tracks in subtitles.values():
        track = _first_vtt_track(tracks)
        if track is not None:
            return track

    return None


def parse_vtt_segments(content: str) -> list[TranscriptSegment]:
    """Parse the minimum WebVTT subset used by YouTube official subtitles."""

    lines = content.replace("\r\n", "\n").replace("\r", "\n").split("\n")
    if lines:
        lines[0] = lines[0].lstrip("\ufeff")

    index = 0
    if lines and lines[0].strip().startswith("WEBVTT"):
        index = 1
        while index < len(lines) and lines[index].strip():
            index += 1

    segments: list[TranscriptSegment] = []
    while index < len(lines):
        while index < len(lines) and not lines[index].strip():
            index += 1
        if index >= len(lines):
            break

        line = lines[index].strip()
        if _is_vtt_metadata_block(line):
            index = _skip_block(lines, index + 1)
            continue

        if VTT_CUE_SEPARATOR in line:
            time_line = line
            index += 1
        else:
            index += 1
            if index >= len(lines):
                break
            time_line = lines[index].strip()
            index += 1

        if VTT_CUE_SEPARATOR not in time_line:
            index = _skip_block(lines, index)
            continue

        start, end = _parse_vtt_time_line(time_line)
        text_lines: list[str] = []
        while index < len(lines) and lines[index].strip():
            text_lines.append(lines[index])
            index += 1

        text = clean_vtt_text(" ".join(text_lines))
        if text:
            segments.append(TranscriptSegment(start=start, end=end, text=text))

    return segments


def clean_vtt_text(text: str) -> str:
    """Remove simple markup and normalize subtitle text."""

    without_tags = re.sub(r"<[^>]+>", "", text)
    unescaped = html.unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def fetch_text(url: str) -> str:
    """Fetch subtitle text without writing subtitle files to disk."""

    if not _is_safe_subtitle_url(url):
        raise TranscriptProviderError(_UNSAFE_SUBTITLE_URL_MESSAGE) from None
    try:
        with urlopen(url, timeout=SUBTITLE_FETCH_TIMEOUT_SECONDS) as response:
            payload = _read_subtitle_body(response)
            return _decode_subtitle_payload(payload, response.headers)
    except TranscriptProviderError:
        raise
    except HTTPError as error:
        status_code = error.code
        _close_response_quietly(error)
        raise PlatformAccessError(
            f"official subtitle VTT fetch failed: HTTP Error {status_code}"
        ) from None
    except URLError as error:
        if isinstance(error.reason, TimeoutError | socket.timeout):
            raise NetworkAccessError(
                "official subtitle VTT fetch failed: request timed out"
            ) from None
        raise NetworkAccessError(
            "official subtitle VTT fetch failed: network request failed"
        ) from None
    except TimeoutError:
        raise NetworkAccessError(
            "official subtitle VTT fetch failed: request timed out"
        ) from None
    except Exception:
        raise NetworkAccessError(
            "official subtitle VTT fetch failed: request failed"
        ) from None


def _redirect_location(headers) -> object:
    """Return the raw redirect target using the standard library lookup."""

    if headers is None:
        return None
    for name in ("location", "uri"):
        try:
            if name in headers:
                return headers[name]
        except TypeError:
            return None
    return None


def _effective_redirect_target(request, raw_location: object) -> str | None:
    """Return the absolute URL the request layer would redirect to.

    Mirrors ``urllib.request.HTTPRedirectHandler.http_error_302``: the raw
    ``Location`` value is parsed, given a ``/`` path when it is authority-only,
    re-serialised, percent-encoded with latin-1 (which is how that layer
    recovers the original bytes), and finally resolved against the URL of the
    request being redirected. Relative, scheme-relative and absolute targets
    all pass through the same resolution, so only the resolved result needs a
    safety verdict.

    ``None`` means the target could not be resolved at all -- a quote,
    encoding or resolution failure -- and the redirect must be refused with
    the stable unsafe-URL error rather than a raw codec error.
    """

    if not isinstance(raw_location, str):
        return None
    base = getattr(request, "full_url", None)
    if not isinstance(base, str):
        return None
    try:
        parts = urlparse(raw_location)
        if parts.scheme not in ("http", "https", "ftp", ""):
            return None
        if not parts.path and parts.netloc:
            parts = list(parts)
            parts[2] = "/"
        quoted = quote(
            urlunparse(parts), encoding="iso-8859-1", safe=string.punctuation
        )
        return urljoin(base, quoted)
    except Exception:
        # Control-flow exceptions are not ``Exception`` subclasses and keep
        # propagating.
        return None


def _is_safe_subtitle_url(url: object) -> bool:
    """Return whether a subtitle URL passes the offline safety checks.

    The verdict is total: any unexpected failure while parsing or
    normalizing fails closed exactly like a rejected URL, so a raw exception
    can never escape the boundary and replace the stable error.
    """

    if not _raw_url_is_usable(url):
        return False
    try:
        return _subtitle_url_checks_pass(url)
    except Exception:
        # Control-flow exceptions are not ``Exception`` subclasses and keep
        # propagating.
        return False


def _raw_url_is_usable(value: object) -> bool:
    """Return whether a raw URL value may be parsed at all.

    Runs on the unstripped input -- the initial URL and the raw redirect
    ``Location`` -- before any ``urlparse``, ``quote`` or ``urljoin``.
    ``urlparse`` removes tab, CR and LF from the whole URL before it splits
    the authority off, so a check performed after parsing never sees those
    three and the request layer still contacts the host they were hiding
    inside. An embedded NUL additionally makes ``socket.inet_aton`` raise a
    raw ``ValueError`` further down.
    """

    if not isinstance(value, str):
        return False
    return not _has_control_characters(value)


def _subtitle_url_checks_pass(url: str) -> bool:
    parsed = urlparse(url)
    host = parsed.hostname
    port = parsed.port
    if parsed.scheme != "https":
        return False
    if not host:
        return False
    if parsed.username is not None or parsed.password is not None:
        return False
    if port not in (None, 443):
        return False
    request_host = _normalized_request_host(parsed.netloc, host)
    if request_host is None:
        return False
    return _is_safe_subtitle_host(request_host)


def _normalized_request_host(netloc: str, host: str) -> str | None:
    """Return the host the HTTP request layer would use, or ``None`` if unsafe.

    ``urllib.request.Request`` percent-decodes the raw authority before the
    host reaches the socket layer, platform resolvers drop a trailing DNS root
    dot, and IDNA maps full-width digits and Unicode label separators onto
    ASCII. The value returned here is what gets validated, so the checks
    always describe the host that would actually be contacted.
    """

    if "%" in netloc:
        # Authority percent encoding is rejected instead of decoded: encoded
        # and decoded forms can disagree about host and port. Path and query
        # percent encoding is not part of the authority and stays usable.
        return None
    if _has_control_characters(netloc):
        # IDNA's ASCII fast path passes already-ASCII labels through without
        # nameprep, so control characters survive normalization and reach the
        # resolver unchanged.
        return None
    try:
        ascii_host = host.encode("idna").decode("ascii")
    except UnicodeError:
        return None
    normalized = ascii_host.rstrip(".")
    if not normalized or _has_control_characters(normalized):
        return None
    return normalized


def _is_safe_subtitle_host(host: str) -> bool:
    """Return whether a normalized request host passes the offline host rules.

    The host has already been IDNA-normalized and had its trailing DNS root
    dots removed, so the reserved ``localhost`` namespace is matched on the
    name the resolver would actually see.
    """

    if _has_control_characters(host):
        # Defence in depth for the final gate: the request layer would pass
        # these straight through, and ``inet_aton`` raises a raw ``ValueError``
        # for an embedded NUL.
        return False
    if _is_localhost_namespace(host):
        # Every spelling of ``localhost`` and its subdomains resolves to
        # loopback on the supported platforms without any lookup of ours.
        return False
    address = _ip_literal_address(host)
    if address is None:
        # Numeric-looking hosts the OS could resolve as legacy IPv4 literals
        # must fail closed; ordinary DNS hostnames pass without resolution.
        return _LEGACY_NUMERIC_IPV4_PATTERN.fullmatch(host) is None
    return not (
        address.is_loopback
        or address.is_private
        or address.is_link_local
        or address.is_multicast
        or address.is_reserved
        or address.is_unspecified
    )


def _has_control_characters(value: str) -> bool:
    """Return whether a value contains an ASCII control character or DEL."""

    return any(ord(character) < 0x20 or ord(character) == 0x7F for character in value)


def _is_localhost_namespace(host: str) -> bool:
    """Return whether a normalized host is ``localhost`` or a subdomain."""

    lowered = host.lower()
    return lowered == "localhost" or lowered.endswith(".localhost")


def _close_response_quietly(response) -> None:
    """Close a response without letting cleanup replace the outcome.

    Cleanup runs alongside whatever the request path is already doing, so a
    close that fails must not replace a stable
    ``TranscriptProviderError``/``PlatformAccessError``/``NetworkAccessError``
    /``URLError``, a control-flow exception, or a successful return value --
    and the underlying close text must stay out of every public error and
    traceback. This is the same policy the HTTP status error path uses, and it
    is idempotent: the standard library already closes a successfully followed
    redirect response once, so a repeated close that fails must not invent a
    new public failure either.
    """

    try:
        response.close()
    except Exception:
        # A failing close must not replace the stable error, and control-flow
        # exceptions must keep propagating.
        pass


def _ip_literal_address(host: str):
    """Return an IP address for modern and legacy numeric literals, else None."""

    try:
        return ipaddress.ip_address(host)
    except ValueError:
        pass
    try:
        return ipaddress.IPv4Address(socket.inet_aton(host))
    except (OSError, ValueError):
        # ``inet_aton`` raises ``ValueError`` for an embedded NUL and
        # ``OSError`` for any other malformed literal. Both mean "not a usable
        # numeric form", so the caller applies the fail-closed numeric rule
        # instead of letting a raw exception escape the validator.
        return None


def _read_subtitle_body(response) -> bytes:
    """Read at most ``MAX_SUBTITLE_RESPONSE_BYTES`` bytes of subtitle body."""

    content_length = response.headers.get("Content-Length")
    if content_length is not None:
        try:
            declared_length = int(content_length)
        except (TypeError, ValueError):
            declared_length = None
        if (
            declared_length is not None
            and declared_length > MAX_SUBTITLE_RESPONSE_BYTES
        ):
            raise TranscriptProviderError(_SUBTITLE_TOO_LARGE_MESSAGE) from None
    payload = response.read(MAX_SUBTITLE_RESPONSE_BYTES + 1)
    if len(payload) > MAX_SUBTITLE_RESPONSE_BYTES:
        raise TranscriptProviderError(_SUBTITLE_TOO_LARGE_MESSAGE) from None
    return payload


def _decode_subtitle_payload(payload: bytes, headers) -> str:
    """Decode a subtitle body, mapping charset failures to a stable error."""

    try:
        charset = headers.get_content_charset() or "utf-8"
        return payload.decode(charset)
    except (LookupError, UnicodeDecodeError):
        raise TranscriptProviderError(_SUBTITLE_ENCODING_MESSAGE) from None


def _first_vtt_track(tracks: object) -> dict[str, object] | None:
    if not isinstance(tracks, list):
        return None
    for track in tracks:
        if isinstance(track, dict) and _is_vtt_track(track):
            return track
    return None


def _is_vtt_track(track: dict[str, object]) -> bool:
    ext = _string_value(track.get("ext")).lower()
    url = _string_value(track.get("url")).lower()
    protocol = _string_value(track.get("protocol")).lower()
    format_note = _string_value(track.get("format")).lower()
    return (
        ext == "vtt"
        or ".vtt" in url
        or "webvtt" in protocol
        or "webvtt" in format_note
    )


def _is_vtt_metadata_block(line: str) -> bool:
    return line.startswith("NOTE") or line in {"STYLE", "REGION"}


def _skip_block(lines: list[str], index: int) -> int:
    while index < len(lines) and lines[index].strip():
        index += 1
    return index


def _parse_vtt_time_line(line: str) -> tuple[str, str]:
    start, remainder = line.split(VTT_CUE_SEPARATOR, 1)
    end = remainder.strip().split()[0]
    return start.strip(), end.strip()


def _string_value(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, str):
        return value
    return str(value)


def _fallback_reason(error: TranscriptProviderError) -> str:
    if isinstance(error, NoOfficialSubtitleError):
        return "no official subtitles found"
    if isinstance(error, UnsupportedSubtitleFormatError):
        return "official subtitles have no VTT/WebVTT track"
    return "transcript provider failed"
