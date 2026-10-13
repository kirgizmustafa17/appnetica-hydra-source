"""Main CLI entry point for the Appnetica Hydra source scraper."""

from __future__ import annotations
import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List, Tuple
import httpx

from scraper.crawler import fetch_sitemap_games, fetch_game_downloads, DEFAULT_USER_AGENT
from scraper.cache import SyncCache
from scraper.torrent import fetch_and_generate_magnet


async def upgrade_cached_torrents(
    cache: SyncCache,
    client: httpx.AsyncClient,
    concurrency: int = 15
) -> int:
    """Find all cached items with torrent/file redirect URLs and upgrade them to magnet links."""
    pending: List[Tuple[Dict[str, Any], str]] = []
    for slug, game_data in cache.data.get("games", {}).items():
        for item in game_data.get("items", []):
            uris = item.get("uris", [])
            for u in uris:
                if u.startswith("magnet:?"):
                    continue
                if "file/" in u or ".torrent" in u or "pb.appnetica.com" in u:
                    pending.append((item, u))
                    break

    if not pending:
        return 0

    print(f"[INFO] Found {len(pending)} cached torrent items to upgrade to magnet links...")
    semaphore = asyncio.Semaphore(concurrency)
    converted = 0
    total = len(pending)

    async def worker(item: Dict[str, Any], url: str):
        nonlocal converted
        async with semaphore:
            magnet = await fetch_and_generate_magnet(client, url, fallback_name=item.get("title", ""))
            if magnet:
                item["uris"] = [magnet]
                converted += 1
            if converted % 100 == 0 or converted == total:
                print(f"[PROGRESS] Converted {converted}/{total} torrents to magnet links...")

    tasks = [worker(item, url) for item, url in pending]
    await asyncio.gather(*tasks)
    print(f"[INFO] Successfully upgraded {converted}/{total} torrent items to magnet links.")
    return converted


async def run_scraper(
    output_path: str = "appnetica.json",
    cache_path: str = ".cache.json",
    concurrency: int = 12,
    limit: int = 0,
    full_scan: bool = False,
    prune: bool = True,
    upgrade_torrents: bool = True
) -> None:
    start_time = time.time()
    cache = SyncCache(cache_path)

    limits = httpx.Limits(max_connections=concurrency * 2, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(limits=limits, headers={"User-Agent": DEFAULT_USER_AGENT}, follow_redirects=True) as client:
        print("[INFO] Fetching sitemap from Appnetica...")
        try:
            sitemap_games = await fetch_sitemap_games(client)
        except Exception as e:
            print(f"[FATAL] Failed to fetch sitemap: {e}")
            sys.exit(1)

        print(f"[INFO] Discovered {len(sitemap_games)} games in sitemap.")

        # Determine which games need updating
        games_to_fetch: List[Tuple[str, str]] = []
        cached_count = 0

        for slug, lastmod in sitemap_games:
            if not full_scan and cache.is_cached_and_current(slug, lastmod):
                cached_count += 1
            else:
                games_to_fetch.append((slug, lastmod))

        print(f"[INFO] {cached_count} games already up-to-date in cache.")
        print(f"[INFO] {len(games_to_fetch)} games require fetching.")

        if limit > 0:
            games_to_fetch = games_to_fetch[:limit]
            print(f"[INFO] Applying limit: only fetching first {limit} games.")

        if games_to_fetch:
            semaphore = asyncio.Semaphore(concurrency)
            total = len(games_to_fetch)
            processed = 0

            async def worker(slug: str, lastmod: str):
                nonlocal processed
                items = await fetch_game_downloads(client, slug, semaphore)
                cache.update_game(slug, lastmod, items)
                processed += 1
                if processed % 50 == 0 or processed == total:
                    print(f"[PROGRESS] Processed {processed}/{total} games ({processed/total*100:.1f}%)")

            tasks = [worker(slug, lastmod) for slug, lastmod in games_to_fetch]
            await asyncio.gather(*tasks)

        # Upgrade existing cached torrents to magnet links if enabled
        if upgrade_torrents:
            await upgrade_cached_torrents(cache, client, concurrency=concurrency)

        # Prune games no longer present in sitemap (only if not running a partial limit)
        if prune and limit == 0:
            all_slugs = {s for s, _ in sitemap_games}
            cache.prune_missing(all_slugs)

        # Save updated cache
        cache.save()

        # Build final Hydra output
        all_downloads = cache.all_download_items()
        hydra_payload: Dict[str, Any] = {
            "name": "Appnetica",
            "downloads": all_downloads
        }

        # Write output file atomically
        temp_output = f"{output_path}.tmp"
        with open(temp_output, "w", encoding="utf-8") as f:
            json.dump(hydra_payload, f, ensure_ascii=False, indent=2)

        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(temp_output, output_path)

        elapsed = time.time() - start_time
        magnet_count = sum(1 for d in all_downloads if any(u.startswith("magnet:?") for u in d.get("uris", [])))
        print("\n=== SUMMARY ===")
        print(f"Total Games in Catalog: {len(cache.data.get('games', {}))}")
        print(f"Total Download Items:   {len(all_downloads)}")
        print(f"Total Magnet Links:     {magnet_count}")
        print(f"Output File:           {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")
        print(f"Elapsed Time:          {elapsed:.2f} seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Appnetica Hydra Source Scraper")
    parser.add_argument("--output", default="appnetica.json", help="Path to output JSON file")
    parser.add_argument("--cache", default=".cache.json", help="Path to cache JSON file")
    parser.add_argument("--concurrency", type=int, default=15, help="Concurrent async requests")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of games to fetch (0 for all)")
    parser.add_argument("--full-scan", action="store_true", help="Force re-fetch of all games, ignoring cache")
    parser.add_argument("--no-prune", dest="prune", action="store_false", help="Do not prune removed games from cache")
    parser.add_argument("--no-magnet", dest="upgrade_torrents", action="store_false", help="Disable magnet upgrade")

    args = parser.parse_args()
    asyncio.run(
        run_scraper(
            output_path=args.output,
            cache_path=args.cache,
            concurrency=args.concurrency,
            limit=args.limit,
            full_scan=args.full_scan,
            prune=args.prune,
            upgrade_torrents=args.upgrade_torrents
        )
    )


if __name__ == "__main__":
    main()
