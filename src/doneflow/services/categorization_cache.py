"""In-memory cache for AI task categorization results."""

from __future__ import annotations

import asyncio
import hashlib
import time
from collections import OrderedDict
from collections.abc import Callable
from threading import RLock
from typing import Any


class CategorizationCache:
    """Cache categorization results without storing raw task text as cache keys.

    The cache uses the SHA-256 hash of each task description as the key, keeping
    raw task text out of internal key storage for LGPD-conscious handling. Entries
    expire after the configured TTL and are evicted with a least-recently-used
    policy when the maximum size is reached.
    """

    def __init__(
        self,
        ttl_seconds: int,
        max_entries: int,
        clock: Callable[[], float] | None = None,
    ) -> None:
        """Initialize the categorization cache.

        Args:
            ttl_seconds: Number of seconds each entry remains valid.
            max_entries: Maximum number of entries retained before LRU eviction.
            clock: Optional clock function for deterministic expiration tests.

        Raises:
            ValueError: If ``ttl_seconds`` or ``max_entries`` is not positive.
        """
        if ttl_seconds <= 0:
            raise ValueError("ttl_seconds must be positive")
        if max_entries <= 0:
            raise ValueError("max_entries must be positive")

        self._ttl_seconds = ttl_seconds
        self._max_entries = max_entries
        self._clock = clock or time.monotonic
        self._entries: OrderedDict[str, tuple[float, dict[str, Any]]] = OrderedDict()
        self._sync_lock = RLock()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0

    @property
    def size(self) -> int:
        """Return the number of currently valid cached entries."""
        with self._sync_lock:
            self._purge_expired()
            return len(self._entries)

    def make_key(self, task_text: str) -> str:
        """Return the SHA-256 hash key for a task description.

        Args:
            task_text: Raw task description to hash.

        Returns:
            Hex digest used as the internal cache key.
        """
        return hashlib.sha256(task_text.encode("utf-8")).hexdigest()

    def get(self, task_text: str) -> dict[str, Any] | None:
        """Return a cached categorization result for task text, if present.

        Args:
            task_text: Raw task description to look up.

        Returns:
            Cached categorization payload, or ``None`` on miss or expiration.
        """
        key = self.make_key(task_text)
        with self._sync_lock:
            entry = self._entries.get(key)
            if entry is None:
                self._misses += 1
                return None

            expires_at, result = entry
            if self._clock() >= expires_at:
                del self._entries[key]
                self._misses += 1
                return None

            self._entries.move_to_end(key)
            self._hits += 1
            return dict(result)

    def set(self, task_text: str, result: dict[str, Any]) -> None:
        """Store a categorization result for task text.

        Args:
            task_text: Raw task description to hash before storage.
            result: Categorization payload to cache.
        """
        key = self.make_key(task_text)
        expires_at = self._clock() + self._ttl_seconds
        with self._sync_lock:
            self._purge_expired()
            self._entries[key] = (expires_at, dict(result))
            self._entries.move_to_end(key)
            while len(self._entries) > self._max_entries:
                self._entries.popitem(last=False)

    async def async_get(self, task_text: str) -> dict[str, Any] | None:
        """Return a cached result using an ``asyncio.Lock`` for async callers.

        Args:
            task_text: Raw task description to look up.

        Returns:
            Cached categorization payload, or ``None`` on miss or expiration.
        """
        async with self._lock:
            return self.get(task_text)

    async def async_set(self, task_text: str, result: dict[str, Any]) -> None:
        """Store a categorization result using an ``asyncio.Lock``.

        Args:
            task_text: Raw task description to hash before storage.
            result: Categorization payload to cache.
        """
        async with self._lock:
            self.set(task_text, result)

    def keys(self) -> list[str]:
        """Return the hashed cache keys currently stored."""
        with self._sync_lock:
            self._purge_expired()
            return list(self._entries.keys())

    def stats(self) -> dict[str, int]:
        """Return cache observability counters.

        Returns:
            Dictionary with hit count, miss count, and current valid size.
        """
        with self._sync_lock:
            self._purge_expired()
            return {"hits": self._hits, "misses": self._misses, "size": len(self._entries)}

    def clear(self) -> None:
        """Remove all cached entries and reset hit/miss counters."""
        with self._sync_lock:
            self._entries.clear()
            self._hits = 0
            self._misses = 0

    def _purge_expired(self) -> None:
        """Remove entries whose TTL has elapsed."""
        now = self._clock()
        expired_keys = [
            key for key, (expires_at, _result) in self._entries.items() if now >= expires_at
        ]
        for key in expired_keys:
            del self._entries[key]
