"""Unit tests for CategorizationCache (TDD RED phase)."""

from __future__ import annotations

import asyncio
import hashlib
from importlib import import_module
from typing import Any

import pytest

from doneflow.models.quadrant import Quadrant


@pytest.fixture
def categorization_cache_class() -> type:
    """Return CategorizationCache class from the services layer."""
    module = import_module("doneflow.services.categorization_cache")
    cache_class = getattr(module, "CategorizationCache", None)

    assert cache_class is not None, "CategorizationCache deve existir na camada de serviços"
    return cache_class


@pytest.fixture
def categorized_result() -> dict[str, Any]:
    """Return a representative categorization payload for cache tests."""
    return {"quadrant": Quadrant.DO_NOW, "confidence": 0.93}


def test_cache_returns_result_for_already_categorized_text_hit(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """Cache should return the stored result when the same task text is requested again."""
    cache = categorization_cache_class(ttl_seconds=300, max_entries=1000)
    task_text = "Enviar proposta urgente para cliente hoje"

    cache.set(task_text, categorized_result)

    assert cache.get(task_text) == categorized_result


def test_cache_returns_none_for_new_text_miss(categorization_cache_class: type) -> None:
    """Cache should return None when a task text has never been categorized."""
    cache = categorization_cache_class(ttl_seconds=300, max_entries=1000)

    assert cache.get("Texto nunca categorizado") is None


def test_cache_uses_sha256_hash_as_key_instead_of_plain_text_for_lgpd(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """Cache keys should be SHA-256 hashes so raw task text is not stored as a key."""
    cache = categorization_cache_class(ttl_seconds=300, max_entries=1000)
    task_text = "Pagar boleto médico com dados pessoais hoje"
    expected_key = hashlib.sha256(task_text.encode("utf-8")).hexdigest()

    cache.set(task_text, categorized_result)

    assert cache.make_key(task_text) == expected_key
    assert task_text not in cache.keys()
    assert expected_key in cache.keys()


def test_cache_expires_entries_after_ai_cache_ttl_seconds(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """Cache should expire entries once AI_CACHE_TTL_SECONDS has elapsed."""
    current_time = 1_000.0

    def fake_clock() -> float:
        return current_time

    cache = categorization_cache_class(ttl_seconds=60, max_entries=1000, clock=fake_clock)
    task_text = "Preparar relatório estratégico"
    cache.set(task_text, categorized_result)

    assert cache.get(task_text) == categorized_result

    current_time += 61.0

    assert cache.get(task_text) is None


def test_cache_does_not_exceed_1000_entries_with_lru_eviction(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """Cache should cap storage at 1000 entries and evict the least recently used item."""
    cache = categorization_cache_class(ttl_seconds=300, max_entries=1000)

    for index in range(1000):
        cache.set(f"Tarefa {index}", {"quadrant": Quadrant.SCHEDULE, "confidence": 0.8})

    assert cache.get("Tarefa 0") == {"quadrant": Quadrant.SCHEDULE, "confidence": 0.8}

    cache.set("Tarefa 1000", categorized_result)

    assert cache.size == 1000
    assert cache.get("Tarefa 1") is None
    assert cache.get("Tarefa 0") == {"quadrant": Quadrant.SCHEDULE, "confidence": 0.8}
    assert cache.get("Tarefa 1000") == categorized_result


def test_cache_hit_and_miss_statistics_are_available(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """Cache should expose hit and miss counters for observability."""
    cache = categorization_cache_class(ttl_seconds=300, max_entries=1000)
    task_text = "Ligar para cliente urgente"

    assert cache.get("texto ausente") is None
    cache.set(task_text, categorized_result)
    assert cache.get(task_text) == categorized_result

    assert cache.stats() == {"hits": 1, "misses": 1, "size": 1}


def test_cache_clear_removes_entries_and_resets_statistics(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """clear should remove cached entries and reset observability counters."""
    cache = categorization_cache_class(ttl_seconds=300, max_entries=1000)
    cache.set("Tarefa importante", categorized_result)
    assert cache.get("Tarefa importante") == categorized_result
    assert cache.get("Tarefa ausente") is None

    cache.clear()

    assert cache.keys() == []
    assert cache.stats() == {"hits": 0, "misses": 0, "size": 0}


def test_cache_rejects_non_positive_ttl(categorization_cache_class: type) -> None:
    """Cache TTL must be positive to avoid immediately stale entries."""
    with pytest.raises(ValueError, match="ttl_seconds must be positive"):
        categorization_cache_class(ttl_seconds=0, max_entries=1000)


def test_cache_rejects_non_positive_max_entries(categorization_cache_class: type) -> None:
    """Cache size must be positive so LRU eviction has a valid bound."""
    with pytest.raises(ValueError, match="max_entries must be positive"):
        categorization_cache_class(ttl_seconds=300, max_entries=0)


def test_cache_async_get_and_set_use_same_storage(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """Async cache helpers should store and retrieve values from the sync cache."""
    cache = categorization_cache_class(ttl_seconds=300, max_entries=1000)

    async def exercise_cache() -> dict[str, Any] | None:
        await cache.async_set("Enviar proposta urgente", categorized_result)
        return await cache.async_get("Enviar proposta urgente")

    assert asyncio.run(exercise_cache()) == categorized_result


def test_cache_returns_defensive_copy_for_cached_results(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """Mutating a returned cache payload should not mutate the stored value."""
    cache = categorization_cache_class(ttl_seconds=300, max_entries=1000)
    task_text = "Enviar proposta urgente"
    cache.set(task_text, categorized_result)

    cached = cache.get(task_text)
    assert cached is not None
    cached["confidence"] = 0.01

    assert cache.get(task_text) == categorized_result


def test_cache_size_keys_and_stats_purge_expired_entries_without_explicit_get(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """Observability helpers should purge expired entries even when get is never called."""
    current_time = 50.0

    def fake_clock() -> float:
        return current_time

    cache = categorization_cache_class(ttl_seconds=10, max_entries=1000, clock=fake_clock)
    cache.set("Revisar roadmap de produto", categorized_result)

    current_time = 61.0

    assert cache.size == 0
    assert cache.keys() == []
    assert cache.stats() == {"hits": 0, "misses": 0, "size": 0}


def test_cache_set_updates_existing_entry_and_keeps_single_lru_slot(
    categorization_cache_class: type,
    categorized_result: dict[str, Any],
) -> None:
    """Replacing an existing key should update the payload without duplicating the entry."""
    cache = categorization_cache_class(ttl_seconds=300, max_entries=2)
    task_text = "Ligar para cliente hoje"
    replacement = {"quadrant": Quadrant.SCHEDULE, "confidence": 0.64}

    cache.set(task_text, categorized_result)
    cache.set(task_text, replacement)

    assert cache.size == 1
    assert cache.get(task_text) == replacement
