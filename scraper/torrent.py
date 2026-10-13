"""BitTorrent decoding and Magnet link generator for Appnetica torrent files."""

from __future__ import annotations
import hashlib
from typing import Any, Dict, List, Optional, Tuple
import urllib.parse
import httpx


def decode_bencode(data: bytes) -> Dict[bytes, Any]:
    """
    Pure Python bencode decoder that preserves raw bytes of the 'info' dictionary
    for accurate SHA1 info_hash calculation.
    """
    def decode_item(idx: int) -> Tuple[Any, int]:
        if idx >= len(data):
            raise ValueError("Unexpected EOF in bencode data")
        b = data[idx]

        # Integer: i<int>e
        if b == 105:  # ord('i')
            idx += 1
            end = data.index(b"e", idx)
            val = int(data[idx:end])
            return val, end + 1

        # String: <length>:<bytes>
        if 48 <= b <= 57:  # '0'..'9'
            colon = data.index(b":", idx)
            length = int(data[idx:colon])
            start = colon + 1
            end = start + length
            if end > len(data):
                raise ValueError("String length exceeds data size")
            return data[start:end], end

        # List: l<items>e
        if b == 108:  # ord('l')
            idx += 1
            items: List[Any] = []
            while data[idx] != 101:  # ord('e')
                item, idx = decode_item(idx)
                items.append(item)
            return items, idx + 1

        # Dictionary: d<key><val>e
        if b == 100:  # ord('d')
            idx += 1
            d: Dict[bytes, Any] = {}
            while data[idx] != 101:  # ord('e')
                key, idx = decode_item(idx)
                val_start = idx
                val, idx = decode_item(idx)
                d[key] = val
                if key == b"info":
                    d[b"__raw_info__"] = data[val_start:idx]
            return d, idx + 1

        raise ValueError(f"Invalid bencode token '{chr(b)}' at index {idx}")

    obj, _ = decode_item(0)
    if not isinstance(obj, dict):
        raise ValueError("Root bencode object is not a dictionary")
    return obj


def torrent_bytes_to_magnet(torrent_bytes: bytes, fallback_name: str = "") -> Optional[str]:
    """
    Extract info_hash, name, and announce trackers from torrent bytes
    and construct a standard magnet: URI.
    """
    try:
        decoded = decode_bencode(torrent_bytes)
        raw_info = decoded.get(b"__raw_info__")
        if not raw_info:
            return None

        info_hash = hashlib.sha1(raw_info).hexdigest()

        # Extract torrent name
        info_dict = decoded.get(b"info", {})
        torrent_name = ""
        if isinstance(info_dict, dict) and b"name" in info_dict:
            raw_name = info_dict[b"name"]
            if isinstance(raw_name, bytes):
                torrent_name = raw_name.decode("utf-8", errors="ignore")

        if not torrent_name:
            torrent_name = fallback_name

        # Extract trackers
        trackers: List[str] = []
        if b"announce" in decoded:
            tr = decoded[b"announce"]
            if isinstance(tr, bytes):
                trackers.append(tr.decode("utf-8", errors="ignore"))

        if b"announce-list" in decoded:
            tiers = decoded[b"announce-list"]
            if isinstance(tiers, list):
                for tier in tiers:
                    if isinstance(tier, list):
                        for item in tier:
                            if isinstance(item, bytes):
                                t_str = item.decode("utf-8", errors="ignore")
                                if t_str and t_str not in trackers:
                                    trackers.append(t_str)

        params: List[str] = [f"xt=urn:btih:{info_hash}"]
        if torrent_name:
            params.append(f"dn={urllib.parse.quote(torrent_name)}")
        for tr in trackers:
            params.append(f"tr={urllib.parse.quote(tr)}")

        return "magnet:?" + "&".join(params)
    except Exception as e:
        print(f"[WARN] Failed to convert torrent to magnet: {e}")
        return None


async def fetch_and_generate_magnet(
    client: httpx.AsyncClient,
    torrent_url: str,
    fallback_name: str = "",
    timeout: float = 15.0
) -> Optional[str]:
    """
    Download a .torrent file from torrent_url and return its magnet link.
    """
    try:
        resp = await client.get(torrent_url, timeout=timeout)
        if resp.status_code != 200:
            return None
        return torrent_bytes_to_magnet(resp.content, fallback_name=fallback_name)
    except Exception as e:
        print(f"[WARN] Failed downloading torrent from {torrent_url}: {e}")
        return None
