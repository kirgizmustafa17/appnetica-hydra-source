"""Crawler module for fetching Appnetica sitemaps and game data."""

from __future__ import annotations
import asyncio
import re
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional, Tuple
import httpx

from scraper.parser import parse_appnetica_game
from scraper.torrent import fetch_and_generate_magnet

SITEMAP_URL = "https://appnetica.com/games.xml"
DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
)


async def fetch_sitemap_games(
    client: httpx.AsyncClient, sitemap_url: str = SITEMAP_URL
) -> List[Tuple[str, str]]:
    """
    Fetch games.xml sitemap and return list of (slug, lastmod).
    """
    response = await client.get(sitemap_url, timeout=30.0)
    response.raise_for_status()

    root = ET.fromstring(response.content)
    namespace = {"ns": "http://www.sitemaps.org/schemas/sitemap/0.9"}

    games: List[Tuple[str, str]] = []
    for url_elem in root.findall("ns:url", namespace):
        loc = url_elem.find("ns:loc", namespace)
        lastmod = url_elem.find("ns:lastmod", namespace)

        if loc is not None and loc.text:
            loc_text = loc.text.strip()
            match = re.search(r"/games/([^/?#]+)", loc_text)
            if match:
                slug = match.group(1).strip()
                lastmod_text = lastmod.text.strip() if lastmod is not None and lastmod.text else ""
                games.append((slug, lastmod_text))

    return games


async def fetch_game_downloads(
    client: httpx.AsyncClient,
    slug: str,
    semaphore: asyncio.Semaphore,
    max_retries: int = 3
) -> List[Dict[str, Any]]:
    """
    Fetch SvelteKit __data.json for a game, parse download items,
    and resolve torrent files to BitTorrent magnet links.
    """
    url = f"https://appnetica.com/games/{slug}/__data.json"
    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "application/json",
        "Referer": f"https://appnetica.com/games/{slug}",
    }

    async with semaphore:
        for attempt in range(1, max_retries + 1):
            try:
                resp = await client.get(url, headers=headers, timeout=20.0)
                if resp.status_code == 404:
                    return []
                resp.raise_for_status()
                data = resp.json()
                downloads = parse_appnetica_game(data, slug=slug)

                # Resolve torrent items to magnet links
                for item in downloads:
                    torrent_url = item.pop("_torrent_url", None)
                    if torrent_url:
                        magnet = await fetch_and_generate_magnet(
                            client, torrent_url, fallback_name=item.get("title", "")
                        )
                        if magnet:
                            item["uris"] = [magnet]

                return downloads
            except (httpx.RequestError, httpx.HTTPStatusError) as e:
                if attempt == max_retries:
                    print(f"[ERROR] Failed {slug} after {max_retries} attempts: {e}")
                    return []
                await asyncio.sleep(0.5 * attempt)
            except Exception as e:
                print(f"[ERROR] Unexpected error parsing {slug}: {e}")
                return []

    return []
