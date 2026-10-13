"""Unit tests for BitTorrent decoder and magnet generator."""

import hashlib
import urllib.parse
from scraper.torrent import decode_bencode, torrent_bytes_to_magnet


def test_decode_bencode_integer_and_string():
    raw = b"d4:name4:test4:sizei12345ee"
    decoded = decode_bencode(raw)
    assert decoded[b"name"] == b"test"
    assert decoded[b"size"] == 12345


def test_torrent_bytes_to_magnet():
    # Construct a valid minimal torrent bencoded structure
    tr1 = b"udp://tracker.example.com:80"
    tr2 = b"http://tracker2.com/announce"
    name = b"My Test Torrent"

    raw_info = b"d4:name" + str(len(name)).encode() + b":" + name + b"12:piece lengthi16384e6:pieces20:12345678901234567890e"
    expected_hash = hashlib.sha1(raw_info).hexdigest()

    raw_torrent = (
        b"d8:announce" + str(len(tr1)).encode() + b":" + tr1 +
        b"13:announce-listll" + str(len(tr1)).encode() + b":" + tr1 + b"el" +
        str(len(tr2)).encode() + b":" + tr2 + b"ee" +
        b"4:info" + raw_info + b"e"
    )

    magnet = torrent_bytes_to_magnet(raw_torrent)
    assert magnet is not None
    assert magnet.startswith("magnet:?")
    assert f"xt=urn:btih:{expected_hash}" in magnet
    assert "dn=My%20Test%20Torrent" in magnet
    assert f"tr={urllib.parse.quote(tr1.decode())}" in magnet
