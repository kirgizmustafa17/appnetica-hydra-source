"""Cache manager for incremental synchronization."""

from __future__ import annotations
import json
import os
from typing import Any, Dict, List, Optional
from scraper.parser import normalize_file_size


class SyncCache:
    """Manages cached game metadata and download items."""

    def __init__(self, cache_file: str = ".cache.json") -> None:
        self.cache_file = cache_file
        self.data: Dict[str, Any] = {
            "last_synced": "",
            "games": {}
        }
        self.load()

    def load(self) -> None:
        """Load cache from disk if it exists."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, "r", encoding="utf-8") as f:
                    content = json.load(f)
                    if isinstance(content, dict):
                        self.data = {
                            "last_synced": content.get("last_synced", ""),
                            "games": content.get("games", {})
                        }
            except Exception as e:
                print(f"[WARN] Failed to load cache file: {e}. Starting fresh.")
                self.data = {"last_synced": "", "games": {}}

    def save(self) -> None:
        """Save cache to disk atomically."""
        temp_file = f"{self.cache_file}.tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)
        if os.path.exists(self.cache_file):
            os.remove(self.cache_file)
        os.rename(temp_file, self.cache_file)

    def is_cached_and_current(self, slug: str, lastmod: str) -> bool:
        """Check if slug exists in cache with the exact same lastmod timestamp."""
        game_entry = self.data["games"].get(slug)
        if not game_entry:
            return False
        cached_lastmod = game_entry.get("lastmod", "")
        return bool(cached_lastmod and cached_lastmod == lastmod and game_entry.get("items"))

    def get_cached_items(self, slug: str) -> List[Dict[str, Any]]:
        """Return cached download items for a slug."""
        game_entry = self.data["games"].get(slug, {})
        return game_entry.get("items", [])

    def update_game(self, slug: str, lastmod: str, items: List[Dict[str, Any]]) -> None:
        """Update or insert game entries."""
        # Ensure sizes are normalized
        for item in items:
            if "fileSize" in item:
                item["fileSize"] = normalize_file_size(item["fileSize"])
        self.data["games"][slug] = {
            "lastmod": lastmod,
            "items": items
        }

    def prune_missing(self, current_slugs: set[str]) -> None:
        """Remove games from cache that are no longer in the sitemap."""
        cached_slugs = list(self.data["games"].keys())
        for slug in cached_slugs:
            if slug not in current_slugs:
                del self.data["games"][slug]

    def normalize_all_sizes(self) -> int:
        """Normalize all file sizes across cached games."""
        normalized_count = 0
        for slug, game_info in self.data.get("games", {}).items():
            for item in game_info.get("items", []):
                orig_size = item.get("fileSize", "")
                norm_size = normalize_file_size(orig_size)
                if orig_size != norm_size:
                    item["fileSize"] = norm_size
                    normalized_count += 1
        return normalized_count

    def all_download_items(self) -> List[Dict[str, Any]]:
        """Collect and return all download items across all games, sorted by title."""
        all_items: List[Dict[str, Any]] = []
        for slug, game_info in self.data["games"].items():
            items = game_info.get("items", [])
            for item in items:
                if "fileSize" in item:
                    item["fileSize"] = normalize_file_size(item["fileSize"])
                all_items.append(item)
        all_items.sort(key=lambda x: x.get("title", "").lower())
        return all_items
