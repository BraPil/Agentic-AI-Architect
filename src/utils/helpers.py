"""
Utility functions shared across the Agentic AI Architect system.

Includes:
  - sanitize_text: Strip potentially malicious content before LLM processing
  - extract_metadata: Parse metadata from raw HTTP response headers / HTML meta tags
  - chunk_text: Fixed-size text chunking
  - hash_content: SHA-256 content fingerprinting
  - retry_with_backoff: Decorator for retrying flaky operations
  - rate_limit: Simple token-bucket rate limiter
"""

import functools
import hashlib
import logging
import re
import time
from collections.abc import Callable
from typing import Any, TypeVar

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


# ---------------------------------------------------------------------------
# Text sanitization (prompt injection defense)
# ---------------------------------------------------------------------------

# Patterns that are hallmarks of prompt injection attempts
_INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?previous\s+instructions?", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+(a\s+)?(?:DAN|jailbreak|unrestricted)", re.IGNORECASE),
    re.compile(r"act\s+as\s+(if\s+)?you\s+(have\s+no\s+)?(?:no\s+)?(?:limits|restrictions)", re.IGNORECASE),
    re.compile(r"<\s*system\s*>", re.IGNORECASE),
    re.compile(r"\[INST\]|\[/INST\]", re.IGNORECASE),
    re.compile(r"###\s*System\s*:", re.IGNORECASE),
]


def sanitize_text(text: str, placeholder: str = "[REDACTED]") -> str:
    """
    Remove or neutralise potential prompt injection patterns from external text.

    This is applied to ALL external content (crawled web pages, tool outputs,
    user-submitted content) before it is included in an LLM prompt.

    Args:
        text: Raw input text that may contain injection attempts.
        placeholder: Replacement string for detected patterns.

    Returns:
        Sanitized text safe for inclusion in an LLM prompt.
    """
    for pattern in _INJECTION_PATTERNS:
        text = pattern.sub(placeholder, text)
    return text


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------

def extract_metadata(html: str, url: str = "") -> dict[str, Any]:
    """
    Extract metadata from an HTML document's <meta> and <title> tags.

    Args:
        html: Raw HTML content.
        url: Source URL for context.

    Returns:
        Dict with keys: title, description, author, published_date, og_image.
    """
    meta: dict[str, Any] = {"url": url}

    # Title
    title_match = re.search(r"<title[^>]*>(.*?)</title>", html, re.IGNORECASE | re.DOTALL)
    if title_match:
        meta["title"] = re.sub(r"\s+", " ", title_match.group(1)).strip()

    # Open Graph / standard meta tags
    _meta_tags = {
        "description": [r'name=["\']description["\'][^>]*content=["\']([^"\']+)',
                         r'content=["\']([^"\']+)[^>]*name=["\']description["\']'],
        "author": [r'name=["\']author["\'][^>]*content=["\']([^"\']+)',
                   r'content=["\']([^"\']+)[^>]*name=["\']author["\']'],
        "og:title": [r'property=["\']og:title["\'][^>]*content=["\']([^"\']+)'],
        "og:description": [r'property=["\']og:description["\'][^>]*content=["\']([^"\']+)'],
        "published_date": [r'(?:datePublished|article:published_time)[^>]*content=["\']([^"\']+)'],
    }

    for key, patterns in _meta_tags.items():
        for pattern in patterns:
            match = re.search(pattern, html, re.IGNORECASE)
            if match:
                meta[key] = match.group(1).strip()
                break

    return meta


# ---------------------------------------------------------------------------
# Text chunking
# ---------------------------------------------------------------------------

def chunk_text(
    text: str,
    chunk_size: int = 400,
    overlap: int = 50,
) -> list[str]:
    """
    Split text into overlapping word-based chunks.

    Args:
        text: Input text to chunk.
        chunk_size: Target word count per chunk.
        overlap: Word overlap between consecutive chunks.

    Returns:
        List of text chunks.
    """
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks: list[str] = []
    start = 0
    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap

    return chunks


# ---------------------------------------------------------------------------
# Content hashing
# ---------------------------------------------------------------------------

def hash_content(content: str) -> str:
    """Return the SHA-256 hex digest of the given string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Retry decorator
# ---------------------------------------------------------------------------

def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[[F], F]:
    """
    Decorator that retries a function on specified exceptions with exponential back-off.

    Args:
        max_attempts: Maximum number of total attempts (including the first).
        initial_delay: Seconds to wait before the first retry.
        backoff_factor: Multiplier applied to the delay after each failure.
        exceptions: Exception types that trigger a retry.

    Usage::

        @retry_with_backoff(max_attempts=3, exceptions=(requests.RequestException,))
        def fetch(url: str) -> str:
            ...
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            delay = initial_delay
            last_exception: Exception | None = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as exc:
                    last_exception = exc
                    if attempt < max_attempts:
                        logger.warning(
                            "Attempt %d/%d for %s failed (%s). Retrying in %.1fs…",
                            attempt,
                            max_attempts,
                            func.__name__,
                            exc,
                            delay,
                        )
                        time.sleep(delay)
                        delay *= backoff_factor
                    else:
                        logger.error(
                            "All %d attempts for %s failed. Last error: %s",
                            max_attempts,
                            func.__name__,
                            exc,
                        )
            if last_exception is not None:
                raise last_exception
        return wrapper  # type: ignore[return-value]
    return decorator


# ---------------------------------------------------------------------------
# Rate limiter (simple token bucket)
# ---------------------------------------------------------------------------

class _TokenBucket:
    """Thread-safe token bucket for rate limiting."""

    def __init__(self, rate: float, capacity: float) -> None:
        self._rate = rate        # tokens per second
        self._capacity = capacity
        self._tokens = capacity
        self._last_refill = time.monotonic()

    def consume(self, tokens: float = 1.0) -> float:
        """Consume tokens, sleeping if necessary. Returns sleep duration."""
        now = time.monotonic()
        elapsed = now - self._last_refill
        self._tokens = min(self._capacity, self._tokens + elapsed * self._rate)
        self._last_refill = now

        if self._tokens >= tokens:
            self._tokens -= tokens
            return 0.0

        wait = (tokens - self._tokens) / self._rate
        time.sleep(wait)
        self._tokens = 0.0
        return wait


_buckets: dict[str, _TokenBucket] = {}


def rate_limit(key: str = "default", calls_per_second: float = 1.0) -> None:
    """
    Block until the rate limit allows another call.

    Uses a named token bucket so different services can have independent limits.

    Args:
        key: Identifier for the rate limit bucket (e.g. ``'openai'``, ``'github'``).
        calls_per_second: Maximum allowed calls per second.
    """
    if key not in _buckets:
        _buckets[key] = _TokenBucket(rate=calls_per_second, capacity=calls_per_second)
    _buckets[key].consume()
