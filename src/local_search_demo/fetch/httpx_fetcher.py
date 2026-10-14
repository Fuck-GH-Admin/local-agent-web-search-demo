"""HTTPX-based HTML downloader. B02 deliberately performs no article extraction.

The downloaded byte stream is shared unchanged (after HTTP content decompression)
with B03 parsers. HTTP status, network errors, size cap, encoding and redirects
are kept separate from later text-extraction quality.
"""
from __future__ import annotations

from dataclasses import dataclass
import codecs
from pathlib import Path
import re
import time
from urllib.parse import urlparse

import httpx

from local_search_demo.schemas import ErrorDetail, FetchResult
from local_search_demo.fetch.public_network import URLPolicyError

DEFAULT_MAX_BYTES = 2 * 1024 * 1024
DEFAULT_TIMEOUT = 8.0
HTML_TYPES = ("text/html", "application/xhtml+xml")
_META_CHARSET = re.compile(
    rb"<meta\s+[^>]*charset\s*=\s*['\"]?\s*([a-zA-Z0-9._-]+)", re.I
)


@dataclass
class FetchedHTML:
    result: FetchResult
    html_bytes: bytes | None = None
    html: str | None = None


def _valid_encoding(name: str | None) -> str | None:
    if not name:
        return None
    try:
        codecs.lookup(name)
        # Nonempty input exercises the decoder, unlike the empty-input fast path.
        # Registered binary codecs and strict-only codecs are not usable here.
        b"a".decode(name, errors="replace")
    except (LookupError, TypeError, UnicodeError):
        return None
    return name


def decode_html(data: bytes, content_type: str | None) -> tuple[str, str]:
    """Prefer HTTP charset, BOM, then HTML meta, and only then UTF-8 fallback."""
    match = re.search(r"charset\s*=\s*['\"]?([^\s;'\"]+)", content_type or "", re.I)
    declared = _valid_encoding(match.group(1) if match else None)
    if declared:
        return data.decode(declared, errors="replace"), declared
    for bom, encoding in (
        (codecs.BOM_UTF8, "utf-8-sig"),
        (codecs.BOM_UTF16_LE, "utf-16"),
        (codecs.BOM_UTF16_BE, "utf-16"),
    ):
        if data.startswith(bom):
            return data.decode(encoding, errors="replace"), encoding
    meta = _META_CHARSET.search(data[:4096])
    declared = _valid_encoding(meta.group(1).decode("ascii") if meta else None)
    if declared:
        return data.decode(declared, errors="replace"), declared
    return data.decode("utf-8", errors="replace"), "utf-8"


def create_http_client(*, trust_env: bool = True) -> httpx.AsyncClient:
    """Reused across fetches. trust_env permits existing system proxy settings."""
    return httpx.AsyncClient(
        timeout=httpx.Timeout(DEFAULT_TIMEOUT),
        limits=httpx.Limits(max_connections=10, max_keepalive_connections=5),
        max_redirects=5,
        follow_redirects=True,
        trust_env=trust_env,
        headers={"User-Agent": "LocalAgentWebSearchDemo/0.1 (+HTML reading feasibility)"},
    )


class HTMLFetcher:
    def __init__(self, client: httpx.AsyncClient):
        self.client = client

    async def fetch(
        self,
        url: str,
        *,
        max_bytes: int = DEFAULT_MAX_BYTES,
        timeout: float = DEFAULT_TIMEOUT,
    ) -> FetchedHTML:
        started = time.perf_counter()
        requested = url.strip()
        result = FetchResult(url_requested=requested)

        def failed(kind: str, message: str, *, status: str = "FAIL") -> FetchedHTML:
            result.status = status
            result.elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
            result.error = ErrorDetail(kind=kind, message=message[:400])
            return FetchedHTML(result=result)

        try:
            parsed = urlparse(requested)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                return failed("INVALID_URL", "Expected absolute http(s) URL")
        except ValueError:
            return failed("INVALID_URL", "Malformed URL")
        if max_bytes <= 0 or timeout <= 0:
            return failed("INVALID_OPTIONS", "max_bytes and timeout must be positive")

        try:
            async with self.client.stream(
                "GET", requested, follow_redirects=True, timeout=timeout,
                headers={"Accept": "text/html,application/xhtml+xml;q=0.9,*/*;q=0.1"},
            ) as response:
                result.url_final = str(response.url)
                result.redirect_history = [str(item.url) for item in response.history]
                result.http_status = response.status_code
                result.content_type = response.headers.get("content-type")
                if response.status_code >= 400:
                    kind = ("RATE_LIMITED" if response.status_code == 429
                            else "HTTP_ERROR")
                    return failed(kind, f"HTTP {response.status_code} from target")
                media_type = (result.content_type or "").split(";", 1)[0].strip().lower()
                if media_type and media_type not in HTML_TYPES:
                    return failed("UNSUPPORTED_CONTENT_TYPE", f"Expected HTML; got {media_type}")
                size_header = response.headers.get("content-length")
                if size_header and size_header.isascii() and size_header.isdecimal():
                    if int(size_header) > max_bytes:
                        return failed("TOO_LARGE", "Content-Length exceeds max_bytes")
                chunks: list[bytes] = []
                size = 0
                async for chunk in response.aiter_bytes():
                    size += len(chunk)
                    if size > max_bytes:
                        result.bytes = size
                        return failed("TOO_LARGE", "Decoded response exceeds max_bytes")
                    chunks.append(chunk)
                blob = b"".join(chunks)
                result.bytes = len(blob)
                if not blob:
                    return failed("EMPTY_BODY", "HTML response contains no bytes", status="EMPTY")
                text, encoding = decode_html(blob, result.content_type)
                result.encoding = encoding
                result.status = "PASS"
                result.elapsed_ms = round((time.perf_counter() - started) * 1000, 3)
                return FetchedHTML(result=result, html_bytes=blob, html=text)
        except URLPolicyError as exc:
            return failed(exc.kind, str(exc))
        except httpx.TimeoutException as exc:
            return failed("TIMEOUT", f"{type(exc).__name__} downloading HTML")
        except httpx.TooManyRedirects:
            return failed("TOO_MANY_REDIRECTS", "Exceeded redirect limit")
        except httpx.DecodingError:
            return failed("TRANSFER_DECODING_ERROR", "Cannot decode HTTP transfer encoding")
        except httpx.InvalidURL:
            return failed("INVALID_URL", "HTTPX rejected URL")
        except httpx.RequestError as exc:
            return failed("NETWORK_ERROR", type(exc).__name__)


def save_html(document: FetchedHTML, output: Path) -> FetchResult:
    """Persist the already-fetched bytes with no additional request or re-encoding."""
    if document.result.status != "PASS" or document.html_bytes is None:
        raise ValueError("Cannot save HTML from a failed fetch")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_bytes(document.html_bytes)
    document.result.html_path = str(output)
    return document.result
