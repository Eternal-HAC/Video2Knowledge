"""Security regression tests for provider input and error boundaries.

All tests are fully offline: yt-dlp, network openers, redirect handlers and
responses are replaced with fakes or ``unittest.mock`` patches.
"""

from __future__ import annotations

import contextlib
import io
import socket
import sys
import traceback
import types
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request
from unittest import mock

from app.downloader import get_metadata_with_provider
from app.errors import (
    MetadataProviderError,
    NetworkAccessError,
    PlatformAccessError,
    TranscriptProviderError,
)
from app.platform_adapter import get_platform_capabilities, resolve_video_source
from app.transcript import (
    MAX_SUBTITLE_RESPONSE_BYTES,
    OFFICIAL_SUBTITLE_PROVIDER_ID,
    _ValidatingRedirectHandler,
    acquire_transcript_with_provider,
    fetch_text,
)


# Authority forms whose HTTP request-layer hostname must never be accepted.
# ``urllib.request.Request`` percent-decodes the raw authority, platform
# resolvers strip the trailing DNS root dot, and IDNA maps full-width digits
# and Unicode label separators onto ASCII, so each entry below reaches
# loopback (or an equivalent unsafe host) even though ``urlparse`` alone does
# not say so.
UNSAFE_AUTHORITIES = [
    "127%2e0%2e0%2e1",  # percent-encoded dots -> 127.0.0.1
    "127%2E0%2E0%2E1",  # upper-case percent-encoded dots
    "%31%32%37.0.0.1",  # percent-encoded digits -> 127.0.0.1
    "%31%32%37%2e1",  # encoded legacy short form -> 127.1
    "127.0.0.1%2e",  # encoded trailing dot
    "127.0.0.1.",  # trailing DNS root dot on a modern literal
    "127.1.",  # trailing dot on a legacy short form
    "2130706433.",  # trailing dot on a decimal 32-bit form
    "0x7f000001.",  # trailing dot on a hex form
    "127。0。0。1",  # ideographic full stop separators
    "127．0．0．1",  # fullwidth full stop separators
    "127｡0｡0｡1",  # halfwidth ideographic full stop separators
    "１２７.０.０.１",  # fullwidth digits
    "１２７。０。０。１",  # fullwidth digits and ideographic separators
    "127\xad.0.0.1",  # ignored code point inside a numeric label
    "[::1]",  # loopback IPv6 literal
    "[fe80::1%25eth0]",  # IPv6 literal with a zone identifier
]

UNSAFE_AUTHORITY_URLS = [f"https://{authority}/sub.vtt" for authority in UNSAFE_AUTHORITIES]

# The whole ``localhost`` namespace resolves to loopback on every supported
# platform, and IDNA/``urlparse`` map the full-width and upper-case spellings
# onto the same name, so each entry below must be rejected as an exact name or
# as a ``*.localhost`` subdomain.
UNSAFE_LOCALHOST_AUTHORITIES = [
    "localhost",
    "localhost.",
    "localhost:443",
    "LOCALHOST",
    "LocalHost.",
    "x.localhost",
    "x.localhost.",
    "a.b.localhost",
    "ｌｏｃａｌｈｏｓｔ",
    "ＬＯＣＡＬＨＯＳＴ",
    "x.ｌｏｃａｌｈｏｓｔ",
]

UNSAFE_LOCALHOST_URLS = [
    f"https://{authority}/sub.vtt" for authority in UNSAFE_LOCALHOST_AUTHORITIES
]

# ASCII control characters and DEL inside the authority must fail closed: the
# IDNA ASCII fast path passes them through unchanged, and ``socket.inet_aton``
# raises a raw ``ValueError`` for an embedded NUL.
UNSAFE_CONTROL_AUTHORITIES = [
    "example.com\x00",
    "example.com\x00.evil",
    "exa\x00mple.com",
    "example.com\x01.evil",
    "example.com\x1f.evil",
    "exa\x7fmple.com",
    "example.com\x7f",
]

UNSAFE_CONTROL_AUTHORITY_URLS = [
    f"https://{authority}/sub.vtt" for authority in UNSAFE_CONTROL_AUTHORITIES
]

# Raw control characters must fail closed *before* any parsing. ``urlparse``
# removes tab, CR and LF from the whole URL before it splits the authority off,
# so a check performed after parsing never sees those three and the request
# layer still ends up contacting the host on either side of them. These entries
# are deliberately raw (never percent-encoded) and sit in the authority, the
# path and the query; legal percent encoding lives in ``SAFE_SUBTITLE_URLS``.
UNSAFE_RAW_CONTROL_URLS = [
    "https://exa\tmple.com/sub.vtt",
    "https://exa\rmple.com/sub.vtt",
    "https://exa\nmple.com/sub.vtt",
    "https://example.com\t/sub.vtt",
    "https://example.com/sub\t.vtt",
    "https://example.com/sub.vtt\t?sig=abc",
    "https://example.com/sub.vtt?sig=a\tb",
    "https://exa\x00mple.com/sub.vtt",
    "https://exa\x7fmple.com/sub.vtt",
    "https://example.com/sub\x00.vtt",
    "https://example.com/sub.vtt?token=sec\x1fret",
]

# Raw ``Location`` values carrying the same characters: the redirect body must
# stay unread and the parent opener must not run.
UNSAFE_CONTROL_LOCATIONS = [
    "https://exa\tmple.com/next.vtt",
    "https://exa\rmple.com/next.vtt",
    "https://exa\nmple.com/next.vtt",
    "/next\t.vtt",
    "//cdn.example.com/next\n.vtt",
    "https://cdn.example.com/next.vtt\t",
    "https://exa\x00mple.com/next.vtt",
    "https://exa\x7fmple.com/next.vtt",
    "https://cdn.example.com/next\x1f.vtt",
]

# Hosts and URLs that must keep working: ordinary DNS names, public literals,
# a trailing DNS root dot on a real name, and percent encoding in the path or
# query (where signed subtitle URLs carry their signature).
SAFE_SUBTITLE_URLS = [
    "https://example.com/sub.vtt",
    "https://cdn.example.com/sub.vtt",
    "https://example.com./sub.vtt",
    "https://xn--r8jz45g.jp/sub.vtt",
    "https://example.com:443/sub.vtt",
    "https://8.8.8.8/sub.vtt",
    "https://134744072/sub.vtt",
    "https://[2001:4860:4860::8888]/sub.vtt",
    "https://example.com/a%20b/sub%2Evtt?x=%31%32%37",
    "https://example.com/sub.vtt?signature=abc%2Fdef%3D&token=x%20y",
    # Names that merely contain the reserved label must not be over-blocked.
    "https://notlocalhost.example.com/sub.vtt",
    "https://localhost.example.com/sub.vtt",
    "https://local.host/sub.vtt",
]


class HostClassificationTests(unittest.TestCase):
    def test_www_youtube_host_is_youtube(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=x")
        self.assertEqual(source.source_type, "url")
        self.assertEqual(source.platform, "youtube")

    def test_mobile_youtube_host_is_youtube(self) -> None:
        source = resolve_video_source("https://m.youtube.com/watch?v=x")
        self.assertEqual(source.platform, "youtube")

    def test_youtu_be_host_is_youtube(self) -> None:
        source = resolve_video_source("https://youtu.be/x")
        self.assertEqual(source.platform, "youtube")

    def test_uppercase_and_trailing_dot_hosts_normalize(self) -> None:
        for url in [
            "https://WWW.YOUTUBE.COM/watch?v=x",
            "https://www.youtube.com./watch?v=x",
            "https://www.youtube.com.../watch?v=x",
            "https://YouTu.Be/x",
        ]:
            with self.subTest(url=url):
                self.assertEqual(resolve_video_source(url).platform, "youtube")

    def test_suffix_confusion_hosts_are_not_youtube(self) -> None:
        for url in [
            "https://notyoutube.com/watch?v=x",
            "https://youtube.com.evil.test/watch?v=x",
            "https://youtu.be.evil.test/x",
        ]:
            with self.subTest(url=url):
                self.assertNotEqual(resolve_video_source(url).platform, "youtube")

    def test_userinfo_url_is_not_recognized_as_youtube(self) -> None:
        source = resolve_video_source("https://user@youtube.com/watch?v=x")

        self.assertNotEqual(source.platform, "youtube")
        self.assertEqual(source.platform, "youtube.com")
        self.assertEqual(source.source_type, "url")

    def test_other_supported_platforms_match_exact_hosts(self) -> None:
        cases = [
            ("https://www.bilibili.com/video/x", "bilibili"),
            ("https://www.tiktok.com/@user/video/1", "tiktok"),
            ("https://vimeo.com/12345", "vimeo"),
            ("https://www.coursera.org/learn/x", "coursera"),
            ("https://www.udemy.com/course/x", "udemy"),
        ]
        for url, platform in cases:
            with self.subTest(url=url):
                self.assertEqual(resolve_video_source(url).platform, platform)

    def test_other_platforms_reject_suffix_confusion(self) -> None:
        cases = [
            ("https://bilibili.com.attacker.test/video/x", "bilibili"),
            ("https://tiktok.com.evil.test/@user", "tiktok"),
            ("https://vimeo.com.evil.test/1", "vimeo"),
            ("https://coursera.org.evil.test/learn/x", "coursera"),
            ("https://udemy.com.evil.test/course/x", "udemy"),
        ]
        for url, platform in cases:
            with self.subTest(url=url):
                self.assertNotEqual(resolve_video_source(url).platform, platform)

    def test_unknown_host_keeps_normalized_hostname_label(self) -> None:
        source = resolve_video_source("https://Example.COM/watch?v=x")
        self.assertEqual(source.source_type, "url")
        self.assertEqual(source.platform, "example.com")

    def test_youtu_be_subdomains_are_not_youtube(self) -> None:
        for url in [
            "https://evil.youtu.be/x",
            "https://www.youtu.be/x",
            "https://a.b.youtu.be/x",
        ]:
            with self.subTest(url=url):
                source = resolve_video_source(url)
                self.assertNotEqual(source.platform, "youtube")
                capabilities = get_platform_capabilities(source.platform)
                self.assertFalse(capabilities.supports_metadata)
                self.assertNotIn("yt-dlp", capabilities.metadata_providers)
                self.assertNotIn("official-subtitles", capabilities.transcript_providers)

    def test_reserved_platform_id_hosts_get_no_capabilities(self) -> None:
        for url in [
            "https://youtube/x",
            "https://bilibili/x",
            "https://tiktok/x",
            "https://user@youtube/x",
            "https://user:pass@tiktok/x",
        ]:
            with self.subTest(url=url):
                source = resolve_video_source(url)
                capabilities = get_platform_capabilities(source.platform)
                self.assertFalse(capabilities.supports_metadata)
                self.assertFalse(capabilities.supports_transcript)
                self.assertEqual(capabilities.metadata_providers, ["mock"])
                self.assertEqual(capabilities.transcript_providers, ["mock"])


class MetadataSanitizationTests(unittest.TestCase):
    def test_extraction_failure_hides_underlying_details(self) -> None:
        sensitive = (
            "https://signed.example/url?token=secret-token-value "
            "C:\\Users\\victim\\private-file"
        )
        source = resolve_video_source("https://www.youtube.com/watch?v=real123")
        fake_module = _fake_ytdlp_module(extract_error=RuntimeError(sensitive))

        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
            with self.assertRaises(MetadataProviderError) as context:
                get_metadata_with_provider(source, provider_name="yt-dlp")

        error = context.exception
        self.assertEqual(str(error), "yt-dlp metadata extraction failed")
        self.assertIsNone(error.__cause__)
        formatted = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        for leaked in [
            "signed.example",
            "token=secret",
            "private-file",
            "Users",
            "RuntimeError",
        ]:
            self.assertNotIn(leaked, formatted)

    def test_unexpected_sanitized_shape_keeps_stable_error(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=real123")
        fake_module = _fake_ytdlp_module(
            raw_info={"id": "real123"},
            sanitized=["not", "a", "dict"],
        )

        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
            with self.assertRaises(MetadataProviderError) as context:
                get_metadata_with_provider(source, provider_name="yt-dlp")

        self.assertEqual(
            str(context.exception),
            "yt-dlp returned metadata in an unexpected shape.",
        )

    def test_raw_metadata_only_keeps_provider_and_minimal_subtitles(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=real123")
        raw_info = {
            "id": "real123",
            "title": "Real Metadata Title",
            "webpage_url": "https://www.youtube.com/watch?v=real123",
            "subtitles": {
                "zh-CN": [
                    {
                        "url": "https://example.com/zh.vtt?signature=secret",
                        "ext": "vtt",
                        "protocol": "m3u8_native",
                        "format": "WebVTT",
                        "headers": {"Cookie": "secret-cookie"},
                        "cookies": [{"name": "session", "value": "secret"}],
                        "fragments": [{"path": "C:\\private"}],
                    }
                ],
                "en": [{"url": "https://example.com/en.vtt", "ext": "vtt"}],
            },
            "requested_formats": [{"url": "https://example.com/video"}],
            "_filename": "C:\\Users\\victim\\video.mp4",
            "http_headers": {"Authorization": "Bearer secret"},
            "automatic_captions": {"en": [{"url": "https://example.com/auto.vtt"}]},
        }
        fake_module = _fake_ytdlp_module(raw_info)

        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
            metadata = get_metadata_with_provider(source, provider_name="yt-dlp")

        self.assertEqual(
            metadata.raw_metadata,
            {
                "provider": "yt-dlp",
                "subtitles": {
                    "zh-CN": [
                        {
                            "url": "https://example.com/zh.vtt?signature=secret",
                            "ext": "vtt",
                            "protocol": "m3u8_native",
                            "format": "WebVTT",
                        }
                    ],
                    "en": [{"url": "https://example.com/en.vtt", "ext": "vtt"}],
                },
            },
        )

    def test_raw_metadata_tolerates_unexpected_subtitle_shapes(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=real123")
        raw_info = {
            "id": "real123",
            "title": "Real Metadata Title",
            "webpage_url": "https://www.youtube.com/watch?v=real123",
            "subtitles": [
                {"zh-CN": [{"url": "https://example.com/bad.vtt", "ext": "vtt"}]}
            ],
        }
        fake_module = _fake_ytdlp_module(raw_info)

        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
            metadata = get_metadata_with_provider(source, provider_name="yt-dlp")

        self.assertEqual(
            metadata.raw_metadata,
            {"provider": "yt-dlp", "subtitles": {}},
        )

    def test_raw_metadata_skips_non_dict_tracks(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=real123")
        raw_info = {
            "id": "real123",
            "title": "Real Metadata Title",
            "webpage_url": "https://www.youtube.com/watch?v=real123",
            "subtitles": {
                "en": [
                    "not-a-track",
                    {"ext": "json3", "url": "https://example.com/en.json3"},
                ],
                "broken": {"not": "a list"},
                42: [{"url": "https://example.com/nolang.vtt", "ext": "vtt"}],
            },
        }
        fake_module = _fake_ytdlp_module(raw_info)

        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
            metadata = get_metadata_with_provider(source, provider_name="yt-dlp")

        self.assertEqual(
            metadata.raw_metadata,
            {
                "provider": "yt-dlp",
                "subtitles": {
                    "en": [{"url": "https://example.com/en.json3", "ext": "json3"}]
                },
            },
        )

    def test_nested_and_non_string_track_values_are_dropped(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=real123")
        raw_info = {
            "id": "real123",
            "title": "Real Metadata Title",
            "webpage_url": "https://www.youtube.com/watch?v=real123",
            "subtitles": {
                "en": [
                    {
                        "url": "https://example.com/en.vtt",
                        "ext": "vtt",
                        "protocol": ["m3u8_native"],
                        "format": {"headers": {"Cookie": "secret-cookie"}},
                        "fragments": [{"path": "C:\\private"}],
                    }
                ]
            },
        }
        fake_module = _fake_ytdlp_module(raw_info)

        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
            metadata = get_metadata_with_provider(source, provider_name="yt-dlp")

        self.assertEqual(
            metadata.raw_metadata,
            {
                "provider": "yt-dlp",
                "subtitles": {
                    "en": [{"url": "https://example.com/en.vtt", "ext": "vtt"}]
                },
            },
        )

    def test_raw_metadata_does_not_share_references_with_provider_info(self) -> None:
        source = resolve_video_source("https://www.youtube.com/watch?v=real123")
        nested_format = {"note": "webvtt"}
        track = {
            "url": "https://example.com/en.vtt",
            "ext": "vtt",
            "format": nested_format,
        }
        raw_info = {
            "id": "real123",
            "title": "Real Metadata Title",
            "webpage_url": "https://www.youtube.com/watch?v=real123",
            "subtitles": {"en": [track]},
        }
        fake_module = _fake_ytdlp_module(raw_info)

        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
            metadata = get_metadata_with_provider(source, provider_name="yt-dlp")

        # Mutating the provider-owned nested value must not affect the output.
        nested_format["note"] = "ATTACKED"
        track["url"] = "https://attacker.example/changed.vtt"

        self.assertEqual(
            metadata.raw_metadata,
            {
                "provider": "yt-dlp",
                "subtitles": {
                    "en": [{"url": "https://example.com/en.vtt", "ext": "vtt"}]
                },
            },
        )

    def test_ytdlp_raw_output_cannot_reach_process_streams(self) -> None:
        sensitive = (
            "ERROR: https://signed.example/url?token=secret-token-value "
            "C:\\Users\\victim\\private-file"
        )
        source = resolve_video_source("https://www.youtube.com/watch?v=real123")
        fake_module = _fake_ytdlp_module(
            extract_error=RuntimeError("boom"),
            log_before_error=sensitive,
        )

        stdout = io.StringIO()
        stderr = io.StringIO()
        with mock.patch.dict(sys.modules, {"yt_dlp": fake_module}):
            with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
                with self.assertRaises(MetadataProviderError) as context:
                    get_metadata_with_provider(source, provider_name="yt-dlp")

        error = context.exception
        self.assertEqual(str(error), "yt-dlp metadata extraction failed")
        self.assertIsNone(error.__cause__)
        for leaked in [
            "signed.example",
            "token=secret",
            "private-file",
            "Users",
            "ERROR",
        ]:
            self.assertNotIn(leaked, stdout.getvalue())
            self.assertNotIn(leaked, stderr.getvalue())

    def test_official_subtitle_provider_works_with_minimal_metadata(self) -> None:
        metadata = _youtube_metadata(
            {
                "provider": "yt-dlp",
                "subtitles": {
                    "zh-CN": [
                        {
                            "url": "https://example.com/zh.vtt",
                            "ext": "vtt",
                            "protocol": "m3u8_native",
                            "format": "WebVTT",
                        }
                    ]
                },
            }
        )
        vtt = """WEBVTT

00:00:01.000 --> 00:00:03.000
Minimal metadata subtitle
"""

        with mock.patch("app.transcript.fetch_text", return_value=vtt) as fetch:
            result = acquire_transcript_with_provider(
                metadata,
                provider_name="official-subtitles",
            )

        fetch.assert_called_once_with("https://example.com/zh.vtt")
        self.assertEqual(result.provider, OFFICIAL_SUBTITLE_PROVIDER_ID)
        self.assertEqual(result.segments[0].text, "Minimal metadata subtitle")


class SubtitleUrlBoundaryTests(unittest.TestCase):
    def test_valid_https_url_reaches_mocked_fetch(self) -> None:
        url = "https://example.com/sub.vtt"
        response = _FakeSubtitleResponse(
            b"WEBVTT\n\n00:00:01.000 --> 00:00:02.000\nHi\n"
        )

        with mock.patch("app.transcript.urlopen", return_value=response) as open_:
            text = fetch_text(url)

        open_.assert_called_once_with(url, timeout=30)
        self.assertIn("WEBVTT", text)

    def test_unsafe_schemes_rejected_before_any_network_call(self) -> None:
        for url in [
            "http://example.com/sub.vtt",
            "file:///C:/secret/sub.vtt",
            "ftp://example.com/sub.vtt",
            "data:text/plain;base64,WEBVTT",
        ]:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                self.assertEqual(
                    str(context.exception),
                    "official subtitle VTT fetch failed: unsafe URL",
                )

    def test_missing_host_userinfo_and_non_443_port_rejected(self) -> None:
        cases = [
            "https:///sub.vtt",
            "https://user@example.com/sub.vtt",
            "https://user:pass@example.com/sub.vtt",
            "https://example.com:8080/sub.vtt",
        ]
        for url in cases:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                self.assertEqual(
                    str(context.exception),
                    "official subtitle VTT fetch failed: unsafe URL",
                )

    def test_rejection_error_does_not_echo_url_or_credentials(self) -> None:
        url = "https://user:pass@example.com:8080/sub.vtt?token=secret"

        with mock.patch("app.transcript.urlopen"):
            with self.assertRaises(TranscriptProviderError) as context:
                fetch_text(url)

        message = str(context.exception)
        self.assertEqual(message, "official subtitle VTT fetch failed: unsafe URL")
        for leaked in ["user", "pass", "token", "secret", "example.com", "8080"]:
            self.assertNotIn(leaked, message)

    def test_explicit_443_port_is_allowed(self) -> None:
        url = "https://example.com:443/sub.vtt"
        response = _FakeSubtitleResponse(b"WEBVTT\n\n")

        with mock.patch("app.transcript.urlopen", return_value=response) as open_:
            fetch_text(url)

        open_.assert_called_once_with(url, timeout=30)

    def test_public_literal_ip_is_allowed(self) -> None:
        url = "https://8.8.8.8/sub.vtt"
        response = _FakeSubtitleResponse(b"WEBVTT\n\n")

        with mock.patch("app.transcript.urlopen", return_value=response) as open_:
            fetch_text(url)

        open_.assert_called_once_with(url, timeout=30)

    def test_restricted_literal_ips_are_rejected(self) -> None:
        cases = [
            "https://127.0.0.1/sub.vtt",  # loopback
            "https://[::1]/sub.vtt",  # loopback
            "https://10.1.2.3/sub.vtt",  # private
            "https://192.168.1.1/sub.vtt",  # private
            "https://172.16.0.1/sub.vtt",  # private
            "https://[fd00::1]/sub.vtt",  # private (unique local)
            "https://169.254.1.1/sub.vtt",  # link-local
            "https://[fe80::1]/sub.vtt",  # link-local
            "https://224.0.0.1/sub.vtt",  # multicast
            "https://240.0.0.1/sub.vtt",  # reserved
            "https://0.0.0.0/sub.vtt",  # unspecified
            "https://[::]/sub.vtt",  # unspecified
        ]
        for url in cases:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                self.assertEqual(
                    str(context.exception),
                    "official subtitle VTT fetch failed: unsafe URL",
                )

    def test_legacy_numeric_loopback_and_private_forms_are_rejected(self) -> None:
        for url in [
            "https://127.1/sub.vtt",  # inet_aton short form -> 127.0.0.1
            "https://127.0.1/sub.vtt",  # inet_aton short form -> 127.0.0.1
            "https://2130706433/sub.vtt",  # decimal 32-bit -> 127.0.0.1
            "https://0177.0.0.1/sub.vtt",  # octal -> 127.0.0.1
            "https://0x7f000001/sub.vtt",  # hex -> 127.0.0.1
            "https://10.1/sub.vtt",  # inet_aton short form -> 10.0.0.1
            "https://99999999999999999999/sub.vtt",  # unparseable numeric: fail closed
        ]:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                self.assertEqual(
                    str(context.exception),
                    "official subtitle VTT fetch failed: unsafe URL",
                )

    def test_legacy_numeric_public_ip_form_is_allowed(self) -> None:
        response = _FakeSubtitleResponse(b"WEBVTT\n\n")

        with mock.patch("app.transcript.urlopen", return_value=response) as open_:
            fetch_text("https://134744072/sub.vtt")

        open_.assert_called_once_with("https://134744072/sub.vtt", timeout=30)

    def test_redirect_to_unsafe_url_rejected_before_second_request(self) -> None:
        handler = _ValidatingRedirectHandler()
        request = _redirect_source_request()
        for newurl in [
            "http://example.com/next.vtt",
            "https://user:pass@example.com/next.vtt",
            "https://example.com:8080/next.vtt",
            "https://127.0.0.1/next.vtt",
            "file:///C:/secret.vtt",
        ]:
            with self.subTest(newurl=newurl):
                with self.assertRaises(TranscriptProviderError) as context:
                    handler.redirect_request(request, None, 302, "Found", {}, newurl)
                self.assertEqual(
                    str(context.exception),
                    "official subtitle VTT fetch failed: unsafe URL",
                )

    def test_redirect_to_valid_https_url_is_allowed(self) -> None:
        handler = _ValidatingRedirectHandler()

        request = handler.redirect_request(
            _redirect_source_request(),
            None,
            302,
            "Found",
            {},
            "https://cdn.example.com/next.vtt",
        )

        self.assertIsNotNone(request)
        self.assertEqual(request.full_url, "https://cdn.example.com/next.vtt")


class RequestAuthoritySemanticsTests(unittest.TestCase):
    """Record the request-layer authority semantics the validator must match.

    These assertions are pure offline parsing/computation: no resolver call and
    no socket is used.
    """

    def test_percent_encoded_authority_reaches_the_request_layer_decoded(self) -> None:
        for url, request_host in [
            ("https://127%2e0%2e0%2e1/sub.vtt", "127.0.0.1"),
            ("https://%31%32%37.0.0.1/sub.vtt", "127.0.0.1"),
            ("https://%31%32%37%2e1/sub.vtt", "127.1"),
            ("https://127.0.0.1%2e/sub.vtt", "127.0.0.1."),
        ]:
            with self.subTest(url=url):
                self.assertNotEqual(urlparse(url).hostname, request_host)
                self.assertEqual(Request(url).host, request_host)

    def test_unicode_authority_normalizes_to_ascii_loopback(self) -> None:
        for authority in [
            "127。0。0。1",
            "127．0．0．1",
            "127｡0｡0｡1",
            "１２７.０.０.１",
            "１２７。０。０。１",
        ]:
            with self.subTest(authority=authority):
                host = urlparse(f"https://{authority}/sub.vtt").hostname
                self.assertNotEqual(host, "127.0.0.1")
                self.assertEqual(host.encode("idna"), b"127.0.0.1")


class AuthorityNormalizationTests(unittest.TestCase):
    """Initial subtitle URLs must not bypass the validator through the authority."""

    def test_encoded_and_unicode_authorities_are_rejected_before_any_request(
        self,
    ) -> None:
        for url in UNSAFE_AUTHORITY_URLS:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                self.assertEqual(
                    str(context.exception),
                    "official subtitle VTT fetch failed: unsafe URL",
                )

    def test_authority_rejection_error_leaks_nothing_from_the_url(self) -> None:
        for url in UNSAFE_AUTHORITY_URLS:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                error = context.exception
                self.assertEqual(
                    error.args, ("official subtitle VTT fetch failed: unsafe URL",)
                )
                self.assertIsNone(error.__cause__)
                formatted = "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )
                self.assertNotIn(url, formatted)

    def test_rejection_error_hides_credentials_and_encoding_marker(self) -> None:
        url = "https://user:pass@127%2e0%2e0%2e1:8443/sub.vtt?token=secret"

        with mock.patch("app.transcript.urlopen") as open_:
            with self.assertRaises(TranscriptProviderError) as context:
                fetch_text(url)

        open_.assert_not_called()
        error = context.exception
        self.assertEqual(
            str(error), "official subtitle VTT fetch failed: unsafe URL"
        )
        formatted = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        for leaked in ["user", "pass", "token", "secret", "127%2e", "8443", "sub.vtt"]:
            self.assertNotIn(leaked, formatted)

    def test_plain_hosts_public_literals_and_signed_queries_still_work(self) -> None:
        for url in SAFE_SUBTITLE_URLS:
            with self.subTest(url=url):
                response = _FakeSubtitleResponse(b"WEBVTT\n\n")
                with mock.patch(
                    "app.transcript.urlopen", return_value=response
                ) as open_:
                    fetch_text(url)
                open_.assert_called_once_with(url, timeout=30)
                self.assertTrue(response.closed)


class LocalhostNamespaceTests(unittest.TestCase):
    """The reserved ``localhost`` namespace must never reach the opener."""

    def test_reserved_namespace_urls_are_rejected_before_any_request(self) -> None:
        for url in UNSAFE_LOCALHOST_URLS:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                self.assertEqual(
                    str(context.exception),
                    "official subtitle VTT fetch failed: unsafe URL",
                )

    def test_reserved_namespace_rejection_leaks_nothing_from_the_url(self) -> None:
        for url in UNSAFE_LOCALHOST_URLS:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                error = context.exception
                self.assertEqual(
                    error.args, ("official subtitle VTT fetch failed: unsafe URL",)
                )
                self.assertIsNone(error.__cause__)
                self.assertIsNone(error.__context__)
                formatted = _formatted_exception(error)
                self.assertNotIn(url, formatted)

    def test_reserved_namespace_with_credentials_leaks_nothing(self) -> None:
        url = "https://user:pass@x.localhost:8443/sub.vtt?token=secret"

        with mock.patch("app.transcript.urlopen") as open_:
            with self.assertRaises(TranscriptProviderError) as context:
                fetch_text(url)

        open_.assert_not_called()
        error = context.exception
        self.assertEqual(
            str(error), "official subtitle VTT fetch failed: unsafe URL"
        )
        formatted = _formatted_exception(error)
        for leaked in [url, "user", "pass", "token", "secret", "8443"]:
            self.assertNotIn(leaked, formatted)


class AuthorityControlCharacterTests(unittest.TestCase):
    """Raw control characters must fail closed before parsing, without a cause."""

    def test_control_characters_in_authority_are_rejected_before_any_request(
        self,
    ) -> None:
        for url in UNSAFE_CONTROL_AUTHORITY_URLS:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                self.assertEqual(
                    str(context.exception),
                    "official subtitle VTT fetch failed: unsafe URL",
                )

    def test_control_character_rejection_never_leaks_a_raw_cause(self) -> None:
        for url in UNSAFE_CONTROL_AUTHORITY_URLS:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                error = context.exception
                self.assertEqual(
                    error.args, ("official subtitle VTT fetch failed: unsafe URL",)
                )
                self.assertIsNone(error.__cause__)
                self.assertIsNone(error.__context__)
                formatted = _formatted_exception(error)
                for leaked in [
                    url,
                    "embedded null character",
                    "ValueError",
                    "OSError",
                    "inet_aton",
                ]:
                    self.assertNotIn(leaked, formatted)

    def test_control_character_authority_with_credentials_leaks_nothing(self) -> None:
        url = "https://user:pass@exa\x00mple.com:8443/sub.vtt?token=secret"

        with mock.patch("app.transcript.urlopen") as open_:
            with self.assertRaises(TranscriptProviderError) as context:
                fetch_text(url)

        open_.assert_not_called()
        error = context.exception
        self.assertEqual(
            str(error), "official subtitle VTT fetch failed: unsafe URL"
        )
        formatted = _formatted_exception(error)
        for leaked in [
            url,
            "user",
            "pass",
            "token",
            "secret",
            "8443",
            "embedded null character",
        ]:
            self.assertNotIn(leaked, formatted)

    def test_raw_control_characters_are_rejected_before_any_parse(self) -> None:
        # ``urlparse`` strips tab/CR/LF from the whole URL before the authority
        # is parsed, so the guard must run on the raw string. ``example.com``
        # on either side of a TAB is exactly the bypass this rejects.
        for url in UNSAFE_RAW_CONTROL_URLS:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                self.assertEqual(
                    context.exception.args,
                    ("official subtitle VTT fetch failed: unsafe URL",),
                )

    def test_raw_control_character_rejection_leaks_nothing(self) -> None:
        for url in UNSAFE_RAW_CONTROL_URLS:
            with self.subTest(url=url):
                with mock.patch("app.transcript.urlopen") as open_:
                    with self.assertRaises(TranscriptProviderError) as context:
                        fetch_text(url)
                open_.assert_not_called()
                error = context.exception
                self.assertEqual(
                    error.args, ("official subtitle VTT fetch failed: unsafe URL",)
                )
                self.assertIsNone(error.__cause__)
                self.assertIsNone(error.__context__)
                formatted = _formatted_exception(error)
                for leaked in [
                    url,
                    "embedded null character",
                    "ValueError",
                    "OSError",
                    "inet_aton",
                ]:
                    self.assertNotIn(leaked, formatted)

    def test_raw_control_character_url_with_credentials_leaks_nothing(self) -> None:
        url = "https://user:pass@exa\tmple.com:8443/sub.vtt?token=secret"

        with mock.patch("app.transcript.urlopen") as open_:
            with self.assertRaises(TranscriptProviderError) as context:
                fetch_text(url)

        open_.assert_not_called()
        error = context.exception
        self.assertEqual(
            str(error), "official subtitle VTT fetch failed: unsafe URL"
        )
        formatted = _formatted_exception(error)
        for leaked in [url, "user", "pass", "token", "secret", "8443"]:
            self.assertNotIn(leaked, formatted)


class ValidatorControlFlowTests(unittest.TestCase):
    """Validation must never swallow control-flow exceptions."""

    def test_control_flow_exceptions_from_the_validator_propagate(self) -> None:
        for raised in (KeyboardInterrupt(), SystemExit(3)):
            with self.subTest(raised=type(raised).__name__):
                with mock.patch(
                    "app.transcript.socket.inet_aton", side_effect=raised
                ):
                    with self.assertRaises(type(raised)):
                        fetch_text("https://example.com/sub.vtt")


class HttpErrorLifecycleTests(unittest.TestCase):
    """The HTTPError conversion path must close, never read, the response."""

    SENSITIVE_URL = "https://example.com/sub.vtt?signature=secret&token=hidden"

    def _error(self, code: int = 429, close_error: BaseException | None = None):
        body = _RecordingErrorBody(close_error=close_error)
        error = HTTPError(self.SENSITIVE_URL, code, "Too Many Requests", None, body)
        return error, body

    def test_http_error_response_is_closed_without_reading_the_body(self) -> None:
        error, body = self._error()

        with mock.patch("app.transcript.urlopen", side_effect=error):
            with self.assertRaises(PlatformAccessError) as context:
                fetch_text(self.SENSITIVE_URL)

        self.assertEqual(
            str(context.exception),
            "official subtitle VTT fetch failed: HTTP Error 429",
        )
        self.assertTrue(body.closed)
        self.assertEqual(body.read_calls, [])

    def test_http_status_code_is_preserved_and_body_untouched_for_all_codes(
        self,
    ) -> None:
        for code in (400, 403, 404, 429, 500, 503):
            with self.subTest(code=code):
                error, body = self._error(code=code)
                with mock.patch("app.transcript.urlopen", side_effect=error):
                    with self.assertRaises(PlatformAccessError) as context:
                        fetch_text(self.SENSITIVE_URL)
                self.assertEqual(
                    str(context.exception),
                    f"official subtitle VTT fetch failed: HTTP Error {code}",
                )
                self.assertTrue(body.closed)
                self.assertEqual(body.read_calls, [])

    def test_close_failure_does_not_override_the_stable_error(self) -> None:
        error, body = self._error(close_error=RuntimeError("raw close failure"))

        with mock.patch("app.transcript.urlopen", side_effect=error):
            with self.assertRaises(PlatformAccessError) as context:
                fetch_text(self.SENSITIVE_URL)

        raised = context.exception
        self.assertEqual(
            str(raised), "official subtitle VTT fetch failed: HTTP Error 429"
        )
        self.assertIsNone(raised.__cause__)
        formatted = "".join(
            traceback.format_exception(type(raised), raised, raised.__traceback__)
        )
        for leaked in [
            "raw close failure",
            "RuntimeError",
            "signature",
            "token",
            "hidden",
            "example.com",
        ]:
            self.assertNotIn(leaked, formatted)
        self.assertTrue(body.closed)

    def test_http_error_without_a_body_is_still_stable(self) -> None:
        error = HTTPError(self.SENSITIVE_URL, 429, "Too Many Requests", None, None)

        with mock.patch("app.transcript.urlopen", side_effect=error):
            with self.assertRaises(PlatformAccessError) as context:
                fetch_text(self.SENSITIVE_URL)

        self.assertEqual(
            str(context.exception),
            "official subtitle VTT fetch failed: HTTP Error 429",
        )

    def test_control_flow_exceptions_from_close_propagate(self) -> None:
        for raised in (KeyboardInterrupt(), SystemExit(3)):
            with self.subTest(raised=type(raised).__name__):
                error, _body = self._error(close_error=raised)
                with mock.patch("app.transcript.urlopen", side_effect=error):
                    with self.assertRaises(type(raised)):
                        fetch_text(self.SENSITIVE_URL)


class SubtitleResponseBoundaryTests(unittest.TestCase):
    def test_content_length_over_limit_rejects_before_reading_body(self) -> None:
        headers = _FakeSubtitleHeaders(
            content_length=str(MAX_SUBTITLE_RESPONSE_BYTES + 1)
        )
        response = _FakeSubtitleResponse(
            b"",
            headers=headers,
            read_error=AssertionError("body must not be read"),
        )

        with mock.patch("app.transcript.urlopen", return_value=response):
            with self.assertRaises(TranscriptProviderError) as context:
                fetch_text("https://example.com/sub.vtt")

        self.assertEqual(
            str(context.exception),
            "official subtitle VTT fetch failed: response too large",
        )
        self.assertEqual(response.read_calls, [])

    def test_oversized_body_rejected_without_content_length(self) -> None:
        body = b"x" * (MAX_SUBTITLE_RESPONSE_BYTES + 1)
        response = _FakeSubtitleResponse(body, headers=_FakeSubtitleHeaders())

        with mock.patch("app.transcript.urlopen", return_value=response):
            with self.assertRaises(TranscriptProviderError) as context:
                fetch_text("https://example.com/sub.vtt")

        self.assertEqual(
            str(context.exception),
            "official subtitle VTT fetch failed: response too large",
        )
        self.assertEqual(response.read_calls, [MAX_SUBTITLE_RESPONSE_BYTES + 1])

    def test_body_exactly_at_limit_is_accepted(self) -> None:
        body = b"WEBVTT\n" + b"x" * (MAX_SUBTITLE_RESPONSE_BYTES - len(b"WEBVTT\n"))
        response = _FakeSubtitleResponse(body, headers=_FakeSubtitleHeaders())

        with mock.patch("app.transcript.urlopen", return_value=response):
            text = fetch_text("https://example.com/sub.vtt")

        self.assertEqual(len(text), MAX_SUBTITLE_RESPONSE_BYTES)
        self.assertEqual(response.read_calls, [MAX_SUBTITLE_RESPONSE_BYTES + 1])

    def test_utf8_vtt_keeps_working(self) -> None:
        vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\n你好 world\n"
        response = _FakeSubtitleResponse(vtt.encode("utf-8"))

        with mock.patch("app.transcript.urlopen", return_value=response):
            text = fetch_text("https://example.com/sub.vtt")

        self.assertIn("你好 world", text)

    def test_legal_non_utf8_charset_is_decoded(self) -> None:
        vtt = "WEBVTT\n\n00:00:01.000 --> 00:00:02.000\ncafé\n"
        response = _FakeSubtitleResponse(
            vtt.encode("latin-1"),
            headers=_FakeSubtitleHeaders(content_charset="latin-1"),
        )

        with mock.patch("app.transcript.urlopen", return_value=response):
            text = fetch_text("https://example.com/sub.vtt")

        self.assertIn("café", text)

    def test_unknown_charset_maps_to_stable_error(self) -> None:
        response = _FakeSubtitleResponse(
            b"WEBVTT\n\n",
            headers=_FakeSubtitleHeaders(content_charset="x-attack-charset"),
        )

        with mock.patch("app.transcript.urlopen", return_value=response):
            with self.assertRaises(TranscriptProviderError) as context:
                fetch_text("https://example.com/sub.vtt")

        message = str(context.exception)
        self.assertEqual(
            message,
            "official subtitle VTT fetch failed: unsupported or invalid subtitle encoding",
        )
        self.assertNotIn("x-attack-charset", message)

    def test_undecodable_body_maps_to_stable_error(self) -> None:
        response = _FakeSubtitleResponse(b"\xff\xfe\x00bad")

        with mock.patch("app.transcript.urlopen", return_value=response):
            with self.assertRaises(TranscriptProviderError) as context:
                fetch_text("https://example.com/sub.vtt")

        message = str(context.exception)
        self.assertEqual(
            message,
            "official subtitle VTT fetch failed: unsupported or invalid subtitle encoding",
        )
        self.assertNotIn("fffe", message)

    def test_body_read_failure_maps_to_stable_network_error(self) -> None:
        response = _FakeSubtitleResponse(
            read_error=OSError("raw low level failure with secret")
        )

        with mock.patch("app.transcript.urlopen", return_value=response):
            with self.assertRaises(NetworkAccessError) as context:
                fetch_text("https://example.com/sub.vtt")

        error = context.exception
        self.assertEqual(
            str(error),
            "official subtitle VTT fetch failed: request failed",
        )
        self.assertIsNone(error.__cause__)
        formatted = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )
        self.assertNotIn("raw low level failure", formatted)

    def test_http_429_classification_is_stable(self) -> None:
        sensitive_url = "https://example.com/sub.vtt?signature=secret&token=hidden"
        error = HTTPError(sensitive_url, 429, "Too Many Requests", hdrs=None, fp=None)

        with mock.patch("app.transcript.urlopen", side_effect=error):
            with self.assertRaises(PlatformAccessError) as context:
                fetch_text(sensitive_url)

        raised = context.exception
        self.assertEqual(
            str(raised),
            "official subtitle VTT fetch failed: HTTP Error 429",
        )
        self.assertIsNone(raised.__cause__)
        formatted = "".join(
            traceback.format_exception(type(raised), raised, raised.__traceback__)
        )
        for leaked in ["signature", "token", "hidden", "Too Many Requests"]:
            self.assertNotIn(leaked, formatted)

    def test_url_error_timeout_classification_is_stable(self) -> None:
        with mock.patch(
            "app.transcript.urlopen",
            side_effect=URLError(socket.timeout("raw timeout secret")),
        ):
            with self.assertRaises(NetworkAccessError) as context:
                fetch_text("https://example.com/sub.vtt")

        raised = context.exception
        self.assertEqual(
            str(raised),
            "official subtitle VTT fetch failed: request timed out",
        )
        self.assertIsNone(raised.__cause__)

    def test_keyboard_interrupt_propagates_unchanged(self) -> None:
        with mock.patch("app.transcript.urlopen", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                fetch_text("https://example.com/sub.vtt")

    def test_system_exit_propagates_unchanged(self) -> None:
        with mock.patch("app.transcript.urlopen", side_effect=SystemExit(3)):
            with self.assertRaises(SystemExit):
                fetch_text("https://example.com/sub.vtt")


class RedirectDispatchTests(unittest.TestCase):
    """Exercise the real redirect handler dispatch, not just validator helpers."""

    REDIRECT_CODES = (301, 302, 303, 307, 308)

    # Raw ``Location`` values that resolve to a safe public HTTPS target once
    # the request layer has quoted and joined them against the source URL.
    SAFE_RELATIVE_LOCATIONS = {
        "/next.vtt": "https://example.com/next.vtt",
        "../next.vtt": "https://example.com/next.vtt",
        "next.vtt": "https://example.com/next.vtt",
        "/a/../b/next.vtt": "https://example.com/b/next.vtt",
        "?sig=abc": "https://example.com/sub.vtt?sig=abc",
        "//cdn.example.com/next.vtt": "https://cdn.example.com/next.vtt",
        "//8.8.8.8/next.vtt": "https://8.8.8.8/next.vtt",
        "//xn--r8jz45g.jp/next.vtt": "https://xn--r8jz45g.jp/next.vtt",
    }

    # Raw ``Location`` values whose effective absolute target stays unsafe.
    UNSAFE_RELATIVE_LOCATIONS = [
        "//127.0.0.1/next.vtt",
        "//127.1/next.vtt",
        "//localhost/next.vtt",
        "//x.localhost/next.vtt",
        "//localhost./next.vtt",
        "https://localhost/next.vtt",
        "https://localhost./next.vtt",
        "https://x.localhost/next.vtt",
        "https://ｌｏｃａｌｈｏｓｔ/next.vtt",
        "//ｌｏｃａｌｈｏｓｔ/next.vtt",
        "//127%2e0%2e0%2e1/next.vtt",
        "//exa\x00mple.com/next.vtt",
        "https://exa\x00mple.com/next.vtt",
        "https://exa\x7fmple.com/next.vtt",
        "https://example.com\x01.evil/next.vtt",
        "//example.com:8443/next.vtt",
        "//user:pass@example.com/next.vtt",
        "http://cdn.example.com/next.vtt",
        "file:///C:/secret.vtt",
        "ftp://cdn.example.com/next.vtt",
        "data:text/plain;base64,WEBVTT",
    ]

    def _prepare(self, code, body=b"", parent_error=None):
        handler = _ValidatingRedirectHandler()
        request = _RedirectSourceRequest()
        fp = _FakeSubtitleResponse(body)
        parent = _RecordingRedirectParent(result="FINAL", error=parent_error)
        handler.parent = parent
        return getattr(handler, f"http_error_{code}"), request, fp, parent

    def _dispatch(self, code, location, body=b"", parent_error=None):
        dispatch, request, fp, parent = self._prepare(code, body, parent_error)
        return dispatch(request, fp, code, "Found", {"location": location}), fp, parent

    def test_safe_redirect_dispatch_bounds_read_and_closes_all_codes(self) -> None:
        for code in self.REDIRECT_CODES:
            with self.subTest(code=code):
                result, fp, parent = self._dispatch(
                    code, "https://cdn.example.com/next.vtt", body=b"redirect body"
                )
                self.assertEqual(result, "FINAL")
                self.assertTrue(fp.closed)
                self.assertNotIn(-1, fp.read_calls)
                self.assertNotIn(None, fp.read_calls)
                self.assertEqual(
                    fp.read_calls, [MAX_SUBTITLE_RESPONSE_BYTES + 1]
                )
                self.assertEqual(len(parent.open_calls), 1)

    def test_unsafe_redirect_dispatch_rejects_and_closes_all_codes(self) -> None:
        for code in self.REDIRECT_CODES:
            with self.subTest(code=code):
                with self.assertRaises(TranscriptProviderError) as context:
                    self._dispatch(code, "http://evil.example/next.vtt")
                error = context.exception
                self.assertEqual(
                    str(error), "official subtitle VTT fetch failed: unsafe URL"
                )
                self.assertIsNone(error.__cause__)
                formatted = "".join(
                    traceback.format_exception(type(error), error, error.__traceback__)
                )
                self.assertNotIn("evil.example", formatted)

    def test_unsafe_redirect_dispatch_makes_no_second_request(self) -> None:
        dispatch, request, fp, parent = self._prepare(302)
        with self.assertRaises(TranscriptProviderError):
            dispatch(
                request,
                fp,
                302,
                "Found",
                {"location": "https://user:pass@example.com:8080/next.vtt?token=secret"},
            )
        self.assertEqual(parent.open_calls, [])
        self.assertEqual(fp.read_calls, [])
        self.assertTrue(fp.closed)

    def test_redirect_rejection_message_does_not_leak_location(self) -> None:
        with self.assertRaises(TranscriptProviderError) as context:
            self._dispatch(
                302, "http://user:pass@evil.example:8080/next.vtt?token=secret"
            )

        message = str(context.exception)
        self.assertEqual(message, "official subtitle VTT fetch failed: unsafe URL")
        for leaked in ["user", "pass", "token", "secret", "evil.example", "8080"]:
            self.assertNotIn(leaked, message)

    def test_oversized_redirect_body_rejected_with_stable_error(self) -> None:
        body = b"x" * (MAX_SUBTITLE_RESPONSE_BYTES + 1)

        with self.assertRaises(TranscriptProviderError) as context:
            self._dispatch(302, "https://cdn.example.com/next.vtt", body=body)

        message = str(context.exception)
        self.assertEqual(
            message, "official subtitle VTT fetch failed: response too large"
        )
        self.assertIsNone(context.exception.__cause__)

    def test_parent_opener_failure_still_closes_redirect_response(self) -> None:
        dispatch, request, fp, parent = self._prepare(
            302, parent_error=URLError("raw low level failure")
        )
        with self.assertRaises(URLError):
            dispatch(
                request,
                fp,
                302,
                "Found",
                {"location": "https://cdn.example.com/next.vtt"},
            )
        self.assertEqual(len(parent.open_calls), 1)
        self.assertTrue(fp.closed)

    def test_legacy_numeric_redirect_targets_rejected_without_second_request(self):
        for location in [
            "https://127.1/next.vtt",
            "https://2130706433/next.vtt",
            "https://0177.0.0.1/next.vtt",
            "https://0x7f000001/next.vtt",
            "https://10.1/next.vtt",
        ]:
            with self.subTest(location=location):
                with self.assertRaises(TranscriptProviderError) as context:
                    self._dispatch(302, location)
                self.assertEqual(
                    str(context.exception),
                    "official subtitle VTT fetch failed: unsafe URL",
                )

    def test_unsafe_authority_redirects_rejected_for_every_redirect_code(self) -> None:
        for code in self.REDIRECT_CODES:
            for location in UNSAFE_AUTHORITY_URLS:
                with self.subTest(code=code, location=location):
                    dispatch, request, fp, parent = self._prepare(code)
                    with self.assertRaises(TranscriptProviderError) as context:
                        dispatch(request, fp, code, "Found", {"location": location})
                    error = context.exception
                    self.assertEqual(
                        str(error), "official subtitle VTT fetch failed: unsafe URL"
                    )
                    self.assertIsNone(error.__cause__)
                    self.assertEqual(parent.open_calls, [])
                    self.assertEqual(fp.read_calls, [])
                    self.assertTrue(fp.closed)

    def test_relative_redirects_resolve_to_the_effective_target(self) -> None:
        """Safe relative and scheme-relative targets resolve, then dispatch."""

        for code in self.REDIRECT_CODES:
            for location, expected in self.SAFE_RELATIVE_LOCATIONS.items():
                with self.subTest(code=code, location=location):
                    dispatch, request, fp, parent = self._prepare(
                        code, body=b"redirect body"
                    )
                    result = dispatch(
                        request, fp, code, "Found", {"location": location}
                    )
                    self.assertEqual(result, "FINAL")
                    self.assertEqual(len(parent.open_calls), 1)
                    self.assertEqual(
                        parent.open_calls[0][0].full_url, expected
                    )
                    self.assertEqual(fp.read_calls, [MAX_SUBTITLE_RESPONSE_BYTES + 1])
                    self.assertTrue(fp.closed)

    def test_unsafe_relative_redirects_rejected_for_every_redirect_code(self) -> None:
        for code in self.REDIRECT_CODES:
            for location in self.UNSAFE_RELATIVE_LOCATIONS:
                with self.subTest(code=code, location=location):
                    dispatch, request, fp, parent = self._prepare(code)
                    with self.assertRaises(TranscriptProviderError) as context:
                        dispatch(request, fp, code, "Found", {"location": location})
                    error = context.exception
                    self.assertEqual(
                        error.args,
                        ("official subtitle VTT fetch failed: unsafe URL",),
                    )
                    self.assertIsNone(error.__cause__)
                    self.assertEqual(parent.open_calls, [])
                    self.assertEqual(fp.read_calls, [])
                    self.assertTrue(fp.closed)

    def test_unsafe_relative_redirect_error_leaks_no_raw_cause(self) -> None:
        for location in [
            "https://exa\x00mple.com/next.vtt",
            "//user:pass@x.localhost:8443/next.vtt?token=secret",
        ]:
            with self.subTest(location=location):
                dispatch, request, fp, parent = self._prepare(302)
                with self.assertRaises(TranscriptProviderError) as context:
                    dispatch(request, fp, 302, "Found", {"location": location})
                error = context.exception
                self.assertEqual(
                    error.args,
                    ("official subtitle VTT fetch failed: unsafe URL",),
                )
                self.assertIsNone(error.__cause__)
                self.assertIsNone(error.__context__)
                formatted = _formatted_exception(error)
                for leaked in [
                    location,
                    "embedded null character",
                    "ValueError",
                    "user",
                    "pass",
                    "token",
                    "secret",
                    "8443",
                ]:
                    self.assertNotIn(leaked, formatted)
                self.assertEqual(parent.open_calls, [])
                self.assertEqual(fp.read_calls, [])
                self.assertTrue(fp.closed)

    def test_redirect_target_the_request_layer_cannot_encode_fails_closed(
        self,
    ) -> None:
        """A target the request layer cannot latin-1 quote maps to unsafe URL."""

        for code in self.REDIRECT_CODES:
            for location in [
                "https://cdn.example.com/日本語.vtt",
                "/日本語.vtt",
                "https://cdn.example.com/next.vtt?q=日本語",
            ]:
                with self.subTest(code=code, location=location):
                    dispatch, request, fp, parent = self._prepare(code)
                    with self.assertRaises(TranscriptProviderError) as context:
                        dispatch(request, fp, code, "Found", {"location": location})
                    error = context.exception
                    self.assertEqual(
                        error.args,
                        ("official subtitle VTT fetch failed: unsafe URL",),
                    )
                    self.assertIsNone(error.__cause__)
                    self.assertIsNone(error.__context__)
                    formatted = _formatted_exception(error)
                    for leaked in [location, "日本語", "latin-1", "codec"]:
                        self.assertNotIn(leaked, formatted)
                    self.assertEqual(parent.open_calls, [])
                    self.assertEqual(fp.read_calls, [])
                    self.assertTrue(fp.closed)

    def test_control_flow_exceptions_in_redirect_resolution_propagate(self) -> None:
        for raised in (KeyboardInterrupt(), SystemExit(3)):
            with self.subTest(raised=type(raised).__name__):
                dispatch, request, fp, parent = self._prepare(302)
                with mock.patch("app.transcript.urljoin", side_effect=raised):
                    with self.assertRaises(type(raised)):
                        dispatch(request, fp, 302, "Found", {"location": "/next.vtt"})
                self.assertEqual(parent.open_calls, [])
                self.assertTrue(fp.closed)

    def test_safe_redirect_with_encoded_path_still_dispatches(self) -> None:
        for code in self.REDIRECT_CODES:
            with self.subTest(code=code):
                location = "https://cdn.example.com/next%20vtt/sub%2Evtt?sig=a%2Fb"
                result, fp, parent = self._dispatch(code, location, body=b"redirect")
                self.assertEqual(result, "FINAL")
                self.assertEqual(len(parent.open_calls), 1)
                self.assertTrue(fp.closed)

    def test_raw_control_locations_rejected_for_every_redirect_code(self) -> None:
        """A raw ``Location`` with any control character never dispatches."""

        for code in self.REDIRECT_CODES:
            for location in UNSAFE_CONTROL_LOCATIONS:
                with self.subTest(code=code, location=location):
                    dispatch, request, fp, parent = self._prepare(code)
                    with self.assertRaises(TranscriptProviderError) as context:
                        dispatch(request, fp, code, "Found", {"location": location})
                    error = context.exception
                    self.assertEqual(
                        error.args,
                        ("official subtitle VTT fetch failed: unsafe URL",),
                    )
                    self.assertIsNone(error.__cause__)
                    self.assertIsNone(error.__context__)
                    formatted = _formatted_exception(error)
                    for leaked in [
                        location,
                        "embedded null character",
                        "ValueError",
                        "inet_aton",
                    ]:
                        self.assertNotIn(leaked, formatted)
                    self.assertEqual(parent.open_calls, [])
                    self.assertEqual(fp.read_calls, [])
                    self.assertTrue(fp.closed)


class RedirectCleanupPrecedenceTests(unittest.TestCase):
    """Redirect cleanup must never replace the outcome it runs alongside."""

    REDIRECT_CODES = (301, 302, 303, 307, 308)
    SAFE_LOCATION = "https://cdn.example.com/next.vtt"
    UNSAFE_LOCATION = "http://evil.example/next.vtt"
    CLOSE_FAILURE = RuntimeError("raw close failure")

    def _prepare(self, body=b"", close_error=None, close_error_after=0,
                 parent_error=None):
        handler = _ValidatingRedirectHandler()
        request = _RedirectSourceRequest()
        fp = _FakeSubtitleResponse(
            body,
            close_error=close_error,
            close_error_after=close_error_after,
        )
        parent = _RecordingRedirectParent(result="FINAL", error=parent_error)
        handler.parent = parent
        return handler, request, fp, parent

    def _dispatch(self, code, location, handler, request, fp):
        return getattr(handler, f"http_error_{code}")(
            request, fp, code, "Found", {"location": location}
        )

    def test_unsafe_redirect_error_survives_a_failing_close(self) -> None:
        for code in self.REDIRECT_CODES:
            with self.subTest(code=code):
                handler, request, fp, parent = self._prepare(
                    close_error=self.CLOSE_FAILURE
                )
                with self.assertRaises(TranscriptProviderError) as context:
                    self._dispatch(
                        code, self.UNSAFE_LOCATION, handler, request, fp
                    )
                error = context.exception
                self.assertEqual(
                    error.args,
                    ("official subtitle VTT fetch failed: unsafe URL",),
                )
                self.assertIsNone(error.__cause__)
                self.assertIsNone(error.__context__)
                formatted = _formatted_exception(error)
                for leaked in ["raw close failure", "RuntimeError", "evil.example"]:
                    self.assertNotIn(leaked, formatted)
                self.assertEqual(parent.open_calls, [])
                self.assertEqual(fp.read_calls, [])
                self.assertTrue(fp.closed)

    def test_oversized_redirect_error_survives_a_failing_close(self) -> None:
        body = b"x" * (MAX_SUBTITLE_RESPONSE_BYTES + 1)
        handler, request, fp, parent = self._prepare(
            body=body, close_error=self.CLOSE_FAILURE
        )

        with self.assertRaises(TranscriptProviderError) as context:
            self._dispatch(302, self.SAFE_LOCATION, handler, request, fp)

        error = context.exception
        self.assertEqual(
            error.args,
            ("official subtitle VTT fetch failed: response too large",),
        )
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)
        formatted = _formatted_exception(error)
        for leaked in ["raw close failure", "RuntimeError"]:
            self.assertNotIn(leaked, formatted)
        self.assertEqual(parent.open_calls, [])
        self.assertTrue(fp.closed)

    def test_parent_failure_survives_a_failing_close(self) -> None:
        for raised in (
            PlatformAccessError("injected platform failure"),
            NetworkAccessError("injected network failure"),
            URLError("injected url failure"),
        ):
            with self.subTest(raised=type(raised).__name__):
                handler, request, fp, parent = self._prepare(
                    close_error=self.CLOSE_FAILURE,
                    close_error_after=1,
                    parent_error=raised,
                )
                with self.assertRaises(type(raised)) as context:
                    self._dispatch(302, self.SAFE_LOCATION, handler, request, fp)
                self.assertIs(context.exception, raised)
                self.assertEqual(len(parent.open_calls), 1)
                self.assertEqual(fp.close_calls, 2)
                self.assertTrue(fp.closed)

    def test_control_flow_exceptions_survive_a_failing_close(self) -> None:
        for raised in (KeyboardInterrupt(), SystemExit(3)):
            with self.subTest(raised=type(raised).__name__):
                handler, request, fp, parent = self._prepare(
                    close_error=self.CLOSE_FAILURE
                )
                with mock.patch("app.transcript.urljoin", side_effect=raised):
                    with self.assertRaises(type(raised)):
                        self._dispatch(302, "/next.vtt", handler, request, fp)
                self.assertEqual(parent.open_calls, [])
                self.assertTrue(fp.closed)

    def test_successful_redirect_survives_a_repeat_close_failure(self) -> None:
        # ``0`` fails the standard library's own close, ``1`` fails only the
        # handler's cleanup close. Neither may replace the returned value.
        for code in self.REDIRECT_CODES:
            for close_error_after in (0, 1):
                with self.subTest(code=code, close_error_after=close_error_after):
                    handler, request, fp, parent = self._prepare(
                        body=b"redirect body",
                        close_error=self.CLOSE_FAILURE,
                        close_error_after=close_error_after,
                    )
                    result = self._dispatch(
                        code, self.SAFE_LOCATION, handler, request, fp
                    )
                    self.assertEqual(result, "FINAL")
                    self.assertEqual(len(parent.open_calls), 1)
                    self.assertEqual(fp.close_calls, 2)
                    self.assertTrue(fp.closed)

    def test_control_flow_exceptions_from_redirect_close_propagate(self) -> None:
        for raised in (KeyboardInterrupt(), SystemExit(3)):
            with self.subTest(raised=type(raised).__name__):
                handler, request, fp, parent = self._prepare(close_error=raised)
                with self.assertRaises(type(raised)):
                    self._dispatch(
                        302, self.UNSAFE_LOCATION, handler, request, fp
                    )
                self.assertEqual(parent.open_calls, [])
                self.assertTrue(fp.closed)

    def test_control_flow_exceptions_from_redirect_cleanup_close_propagate(
        self,
    ) -> None:
        for raised in (KeyboardInterrupt(), SystemExit(3)):
            with self.subTest(raised=type(raised).__name__):
                handler, request, fp, parent = self._prepare(
                    body=b"redirect body", close_error=raised, close_error_after=1
                )
                with self.assertRaises(type(raised)):
                    self._dispatch(302, self.SAFE_LOCATION, handler, request, fp)
                self.assertEqual(fp.close_calls, 2)


def _formatted_exception(error: BaseException) -> str:
    """Return the formatted traceback used for leak assertions."""

    return "".join(traceback.format_exception(type(error), error, error.__traceback__))


def _redirect_source_request():
    request = mock.Mock()
    request.get_method.return_value = "GET"
    request.headers = {}
    return request


class _RedirectSourceRequest:
    """Minimal request double able to pass stdlib redirect dispatch."""

    def __init__(self, full_url="https://example.com/sub.vtt"):
        self.full_url = full_url
        self.headers = {}
        self.timeout = 30
        self.origin_req_host = "example.com"

    def get_method(self):
        return "GET"


class _RecordingRedirectParent:
    def __init__(self, result=None, error=None):
        self.open_calls = []
        self._result = result
        self._error = error

    def open(self, request, timeout=None):
        self.open_calls.append((request, timeout))
        if self._error is not None:
            raise self._error
        return self._result


def _fake_ytdlp_module(
    raw_info: dict[str, object] | None = None,
    extract_error: Exception | None = None,
    sanitized: object = None,
    log_before_error: str | None = None,
):
    class FakeYoutubeDL:
        def __init__(self, opts):
            self.opts = opts

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def extract_info(self, url, download):
            if log_before_error is not None:
                # Mimic real yt-dlp: use the injected logger when present,
                # otherwise fall back to writing raw output to stderr.
                logger = self.opts.get("logger")
                if logger is not None:
                    logger.error(log_before_error)
                else:
                    sys.stderr.write(log_before_error + "\n")
            if extract_error is not None:
                raise extract_error
            return raw_info

        def sanitize_info(self, info):
            if sanitized is not None:
                return sanitized
            return info

    return types.SimpleNamespace(YoutubeDL=FakeYoutubeDL)


def _youtube_metadata(raw_metadata: dict[str, object]):
    from app.downloader import get_mock_metadata

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


class _FakeSubtitleHeaders:
    def __init__(self, content_charset=None, content_length=None):
        self._content_charset = content_charset
        self._content_length = content_length

    def get(self, name, default=None):
        if name.lower() == "content-length":
            return self._content_length
        return default

    def get_content_charset(self):
        return self._content_charset


class _FakeSubtitleResponse:
    def __init__(
        self,
        body: bytes = b"",
        headers=None,
        read_error=None,
        close_error: BaseException | None = None,
        close_error_after: int = 0,
    ):
        self._body = body
        self.headers = headers if headers is not None else _FakeSubtitleHeaders()
        self._read_error = read_error
        self.read_calls: list[int] = []
        self.close_calls = 0
        self.closed = False
        self._close_error = close_error
        self._close_error_after = close_error_after

    def read(self, amt=-1):
        self.read_calls.append(amt)
        if self._read_error is not None:
            raise self._read_error
        if amt is None or amt < 0:
            return self._body
        return self._body[:amt]

    def close(self):
        self.close_calls += 1
        self.closed = True
        if (
            self._close_error is not None
            and self.close_calls > self._close_error_after
        ):
            raise self._close_error

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        self.closed = True
        return False


class _RecordingErrorBody:
    """HTTP error response double recording reads, closes and close failures."""

    def __init__(self, close_error: BaseException | None = None):
        self.read_calls: list[int] = []
        self.closed = False
        self._close_error = close_error

    def read(self, amt=-1):
        self.read_calls.append(amt)
        return b""

    def close(self):
        self.closed = True
        if self._close_error is not None:
            raise self._close_error


if __name__ == "__main__":
    unittest.main()
