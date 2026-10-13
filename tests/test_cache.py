"""Unit tests for SyncCache."""

import os
import tempfile
from scraper.cache import SyncCache


def test_sync_cache_lifecycle():
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_file = os.path.join(tmpdir, "test_cache.json")
        cache = SyncCache(cache_file)

        assert not cache.is_cached_and_current("game-1", "2026-01-01")

        # Update game
        items = [{"title": "Game 1", "uris": ["http://link.com"]}]
        cache.update_game("game-1", "2026-01-01", items)
        cache.save()

        # Reload cache
        cache2 = SyncCache(cache_file)
        assert cache2.is_cached_and_current("game-1", "2026-01-01")
        assert not cache2.is_cached_and_current("game-1", "2026-01-02")
        assert len(cache2.get_cached_items("game-1")) == 1

        # Test pruning
        cache2.prune_missing({"other-game"})
        assert "game-1" not in cache2.data["games"]
        assert len(cache2.all_download_items()) == 0
