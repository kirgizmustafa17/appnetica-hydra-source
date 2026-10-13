"""Main CLI entry point for the Appnetica Hydra source scraper."""

from __future__ import annotations
import argparse
import asyncio
import json
import os
import sys
import time
from typing import Any, Dict, List
import httpx

from scraper.crawler import fetch_sitemap_games, fetch_game_downloads, DEFAULT_USER_AGENT
from scraper.cache import SyncCache


async def run_scraper(
    output_path: str = "appnetica.json",
    cache_path: str = ".cache.json",
    concurrency: int = 12,
    limit: int = 0,
    full_scan: bool = False,
    prune: bool = True
) -> None:
    start_time = time.time()
    cache = SyncCache(cache_path)

    limits = httpx.Limits(max_connections=concurrency * 2, max_keepalive_connections=concurrency)
    async with httpx.AsyncClient(limits=limits, headers={"User-Agent": DEFAULT_USER_AGENT}) as client:
        print("[INFO] Fetching sitemap from Appnetica...")
        try:
            sitemap_games = await fetch_sitemap_games(client)
        except Exception as e:
            print(f"[FATAL] Failed to fetch sitemap: {e}")
            sys.exit(1)

        print(f"[INFO] Discovered {len(sitemap_games)} games in sitemap.")

        # Determine which games need updating
        games_to_fetch: List[tuple[str, str]] = []
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
        print("\n=== SUMMARY ===")
        print(f"Total Games in Catalog: {len(cache.data.get('games', {}))}")
        print(f"Total Download Items:   {len(all_downloads)}")
        print(f"Output File:           {output_path} ({os.path.getsize(output_path) / 1024:.1f} KB)")
        print(f"Elapsed Time:          {elapsed:.2f} seconds")


def main() -> None:
    parser = argparse.ArgumentParser(description="Appnetica Hydra Source Scraper")
    parser.add_argument("--output", default="appnetica.json", help="Path to output JSON file")
    parser.add_argument("--cache", default=".cache.json", help="Path to cache JSON file")
    parser.add_argument("--concurrency", type=int, default=12, help="Concurrent async requests")
    parser.add_argument("--limit", type=int, default=0, help="Limit number of games to fetch (0 for all)")
    parser.add_argument("--full-scan", action="store_true", help="Force re-fetch of all games, ignoring cache")
    parser.add_argument("--no-prune", dest="prune", action="store_false", help="Do not prune removed games from cache")

    args = parser.parse_args()
    asyncio.run(
        run_scraper(
            output_path=args.output,
            cache_path=args.cache,
            concurrency=args.concurrency,
            limit=args.limit,
            full_scan=args.full_scan,
            prune=args.prune
        )
    )


if __name__ == "__main__":
    main()
