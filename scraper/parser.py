"""Parser module for Appnetica SvelteKit SSR JSON data."""

from __future__ import annotations
from typing import Any, Dict, List, Optional


def _normalize_iso_date(date_str: str) -> str:
    """Normalize date strings like '2026-10-12 16:47:07.965Z' to ISO 8601 '2026-10-12T16:47:07.965Z'."""
    if not date_str:
        return ""
    date_str = str(date_str).strip()
    if " " in date_str and "T" not in date_str:
        date_str = date_str.replace(" ", "T", 1)
    return date_str


def _resolve_val(val: Any, data_pool: List[Any]) -> Any:
    """Resolve an index pointer within the SvelteKit deval data pool."""
    if isinstance(val, int) and 0 <= val < len(data_pool):
        return data_pool[val]
    return val


def parse_appnetica_game(data: Dict[str, Any], slug: str = "") -> List[Dict[str, Any]]:
    """
    Parse Appnetica __data.json and extract Hydra-compatible download items.

    Returns:
        List of dicts formatted as:
        [
            {
                "title": "Game Name",
                "fileSize": "600 MB",
                "uris": ["https://cloud.mail.ru/..."],
                "uploadDate": "2026-10-12T16:47:07.965Z"
            },
            ...
        ]
    """
    nodes = data.get("nodes", [])
    if not nodes:
        return []

    # Find the node containing the game record
    target_data_pool: Optional[List[Any]] = None
    for node in reversed(nodes):
        if not node or not isinstance(node, dict):
            continue
        d = node.get("data")
        if isinstance(d, list) and len(d) > 0:
            root = d[0]
            if isinstance(root, dict) and "game" in root:
                target_data_pool = d
                break

    if not target_data_pool:
        # Fallback: check all nodes for any dict containing 'game'
        for node in nodes:
            if not node or not isinstance(node, dict):
                continue
            d = node.get("data")
            if isinstance(d, list) and len(d) > 0 and isinstance(d[0], dict) and "game" in d[0]:
                target_data_pool = d
                break

    if not target_data_pool:
        return []

    d = target_data_pool
    root = d[0]
    game_idx = root.get("game")
    if not isinstance(game_idx, int) or game_idx >= len(d):
        return []

    game = d[game_idx]
    if not isinstance(game, dict):
        return []

    game_id = str(_resolve_val(game.get("id", ""), d))
    raw_title = str(_resolve_val(game.get("title", ""), d)).strip()
    if not raw_title and slug:
        raw_title = slug.replace("-", " ").title()

    game_updated = str(_resolve_val(game.get("updated", ""), d))
    game_created = str(_resolve_val(game.get("created", ""), d))
    default_date = _normalize_iso_date(game_updated or game_created)

    # Locate expanded files
    expand_raw = game.get("expand")
    expand_obj = _resolve_val(expand_raw, d) if expand_raw is not None else {}
    if not isinstance(expand_obj, dict):
        expand_obj = {}

    files_ref = expand_obj.get("files")
    files_list_raw = _resolve_val(files_ref, d) if files_ref is not None else None

    if not isinstance(files_list_raw, list):
        # Check if direct 'files' array in game holds ids or entries
        direct_files = game.get("files")
        files_list_raw = _resolve_val(direct_files, d) if direct_files is not None else []

    if not isinstance(files_list_raw, list):
        files_list_raw = []

    downloads: List[Dict[str, Any]] = []

    for item in files_list_raw:
        file_obj = _resolve_val(item, d)
        if not isinstance(file_obj, dict):
            # If it's just an id string
            if isinstance(file_obj, str) and file_obj and game_id:
                uri = f"https://appnetica.com/file/{file_obj}?game={game_id}"
                downloads.append({
                    "title": raw_title,
                    "fileSize": "Unknown",
                    "uris": [uri],
                    "uploadDate": default_date
                })
            continue

        active = file_obj.get("active", True)
        if active is False:
            continue

        file_id = str(_resolve_val(file_obj.get("id", ""), d))
        file_link = str(_resolve_val(file_obj.get("file_link", ""), d)).strip()
        file_direct = str(_resolve_val(file_obj.get("file_direct", ""), d)).strip()
        label = str(_resolve_val(file_obj.get("label", ""), d)).strip()
        raw_os = str(_resolve_val(file_obj.get("os", ""), d)).strip().lower()
        size = str(_resolve_val(file_obj.get("size", ""), d)).strip()
        file_updated = str(_resolve_val(file_obj.get("updated", ""), d)).strip()
        upload_date = _normalize_iso_date(file_updated) or default_date

        # Determine download URIs: prioritize direct cloud.mail.ru link
        uris: List[str] = []
        if file_link and file_link.startswith("http"):
            uris.append(file_link)
        elif file_direct and file_direct.startswith("http"):
            uris.append(file_direct)
        elif file_id and game_id:
            uris.append(f"https://appnetica.com/file/{file_id}?game={game_id}")

        if not uris:
            continue

        # Format title based on OS and content type
        title_suffix = ""
        if "linux" in raw_os:
            title_suffix = " [Linux]"
        elif "bonus" in raw_os or "bonus" in label.lower() or "soundtrack" in label.lower() or "artbook" in label.lower():
            title_suffix = " [Bonus]"
        elif "mac" in raw_os or "osx" in raw_os:
            title_suffix = " [Mac]"
        elif "android" in raw_os:
            title_suffix = " [Android]"

        final_title = f"{raw_title}{title_suffix}"

        downloads.append({
            "title": final_title,
            "fileSize": size or "Unknown",
            "uris": uris,
            "uploadDate": upload_date
        })

    # If game has no files in expand, check if there's a fallback redirect link
    if not downloads and game_id:
        # Check files array of ids
        game_files_ids = game.get("files")
        resolved_ids = _resolve_val(game_files_ids, d)
        if isinstance(resolved_ids, list):
            for fid in resolved_ids:
                fid_str = str(_resolve_val(fid, d))
                if fid_str:
                    downloads.append({
                        "title": raw_title,
                        "fileSize": "Unknown",
                        "uris": [f"https://appnetica.com/file/{fid_str}?game={game_id}"],
                        "uploadDate": default_date
                    })

    return downloads
