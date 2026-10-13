"""Unit tests for Appnetica parser."""

import pytest
from scraper.parser import parse_appnetica_game, _normalize_iso_date


def test_normalize_iso_date():
    assert _normalize_iso_date("2026-10-12 16:47:07.965Z") == "2026-10-12T16:47:07.965Z"
    assert _normalize_iso_date("2026-10-12T16:47:07.965Z") == "2026-10-12T16:47:07.965Z"
    assert _normalize_iso_date("") == ""


def test_parse_magical_blush():
    sample_data = {
        "type": "data",
        "nodes": [
            None,
            None,
            {
                "type": "data",
                "data": [
                    {"game": 1},
                    {
                        "id": "game_123",
                        "title": "Magical Blush",
                        "updated": "2026-10-11 11:46:44.618Z",
                        "expand": 2
                    },
                    {
                        "files": 3
                    },
                    [4],
                    {
                        "id": "1jcr2usdgdv0hah",
                        "active": True,
                        "file_link": "https://cloud.mail.ru/public/LFs1/9WTdQg8m4",
                        "label": "Mail Cloud (Setup+MD5)",
                        "os": "win",
                        "size": "200 MB",
                        "updated": "2026-10-11 11:46:44.618Z"
                    }
                ]
            }
        ]
    }

    results = parse_appnetica_game(sample_data, slug="magical-blush")
    assert len(results) == 1
    assert results[0]["title"] == "Magical Blush"
    assert results[0]["fileSize"] == "200 MB"
    assert results[0]["uris"] == ["https://cloud.mail.ru/public/LFs1/9WTdQg8m4"]
    assert results[0]["uploadDate"] == "2026-10-11T11:46:44.618Z"


def test_parse_multi_platform_game():
    sample_data = {
        "type": "data",
        "nodes": [
            None,
            None,
            {
                "type": "data",
                "data": [
                    {"game": 1},
                    {
                        "id": "vo7hf5e13jyjgf8",
                        "title": "Stones Keeper Directors Cut",
                        "updated": "2026-10-12 16:47:23.283Z",
                        "expand": 2
                    },
                    {
                        "files": 3
                    },
                    [4, 5, 6],
                    {
                        "id": "sl22pyi77z7wtrq",
                        "active": True,
                        "file_link": "https://cloud.mail.ru/public/xhUe/Bc5RVb1tm",
                        "label": "Mail Cloud (Setup+MD5)",
                        "os": "win",
                        "size": "600 MB",
                        "updated": "2026-10-12 16:47:07.965Z"
                    },
                    {
                        "id": "s3tkdgr3gxsl7d1",
                        "active": True,
                        "file_link": "https://cloud.mail.ru/public/oWQ4/jBpwKNPmA",
                        "label": "Mail Cloud",
                        "os": "bonus",
                        "size": "300 MB",
                        "updated": "2026-10-12 16:47:07.965Z"
                    },
                    {
                        "id": "z6qv7hmkun7239a",
                        "active": True,
                        "file_link": "https://cloud.mail.ru/public/qbfS/U56GVCzne",
                        "label": "Mail Cloud",
                        "os": "linux",
                        "size": "600 MB",
                        "updated": "2026-10-12 16:47:07.972Z"
                    }
                ]
            }
        ]
    }

    results = parse_appnetica_game(sample_data, slug="stones-keeper-directors-cut")
    assert len(results) == 3
    # Check Windows main file
    assert results[0]["title"] == "Stones Keeper Directors Cut"
    assert results[0]["fileSize"] == "600 MB"
    assert results[0]["uris"] == ["https://cloud.mail.ru/public/xhUe/Bc5RVb1tm"]

    # Check Bonus file
    assert results[1]["title"] == "Stones Keeper Directors Cut [Bonus]"
    assert results[1]["fileSize"] == "300 MB"
    assert results[1]["uris"] == ["https://cloud.mail.ru/public/oWQ4/jBpwKNPmA"]

    # Check Linux file
    assert results[2]["title"] == "Stones Keeper Directors Cut [Linux]"
    assert results[2]["fileSize"] == "600 MB"
    assert results[2]["uris"] == ["https://cloud.mail.ru/public/qbfS/U56GVCzne"]


def test_parse_fallback_redirect_url():
    sample_data = {
        "type": "data",
        "nodes": [
            None,
            {
                "type": "data",
                "data": [
                    {"game": 1},
                    {
                        "id": "game_abc",
                        "title": "Fallback Game",
                        "updated": "2026-10-10 10:00:00.000Z",
                        "expand": 2
                    },
                    {
                        "files": 3
                    },
                    [4],
                    {
                        "id": "file_xyz",
                        "active": True,
                        "file_link": "",
                        "file_direct": "",
                        "label": "Download",
                        "os": "win",
                        "size": "1.2 GB"
                    }
                ]
            }
        ]
    }

    results = parse_appnetica_game(sample_data, slug="fallback-game")
    assert len(results) == 1
    assert results[0]["title"] == "Fallback Game"
    assert results[0]["uris"] == ["https://appnetica.com/file/file_xyz?game=game_abc"]
    assert results[0]["fileSize"] == "1.2 GB"
