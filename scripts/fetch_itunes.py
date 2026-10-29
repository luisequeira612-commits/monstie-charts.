#!/usr/bin/env python3
"""Recopila canciones de BABYMONSTER presentes en el chart mundial de iTunes de Kworb."""
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

URL = "https://kworb.net/ww/"
OUTPUT = Path("data/itunes-charts.json")


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables, self.table, self.row, self.cell = [], None, None, None
        self.active = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.active, self.table = True, []
        elif self.active and tag == "tr":
            self.row = []
        elif self.active and tag in ("td", "th"):
            self.cell = []

    def handle_data(self, data):
        if self.active and self.cell is not None:
            self.cell.append(data)

    def handle_endtag(self, tag):
        if self.active and tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif self.active and tag == "tr" and self.row is not None:
            self.table.append(self.row)
            self.row = None
        elif tag == "table" and self.active:
            self.tables.append(self.table)
            self.table, self.active = None, False


def integer(value):
    digits = re.sub(r"[^0-9]", "", value or "")
    return int(digits) if digits else None


def parse_chart(html):
    parser = TableParser()
    parser.feed(html)
    results = []
    for table in parser.tables:
        if not table:
            continue
        headers = [cell.strip().casefold() for cell in table[0]]
        rank_col = next((i for i, h in enumerate(headers) if h in ("pos", "position", "rank")), None)
        title_col = next((i for i, h in enumerate(headers) if "song" in h or "title" in h or h == "track"), None)
        points_col = next((i for i, h in enumerate(headers) if "point" in h), None)
        if title_col is None:
            continue
        for row in table[1:]:
            if title_col >= len(row):
                continue
            title = row[title_col].strip()
            if "babymonster" not in title.casefold():
                continue
            rank = integer(row[rank_col]) if rank_col is not None and rank_col < len(row) else None
            points = integer(row[points_col]) if points_col is not None and points_col < len(row) else None
            results.append({"title": title, "rank": rank, "points": points, "source": URL})
        if results:
            break
    return results


def main():
    request = urllib.request.Request(URL, headers={"User-Agent": "MONSTIE-CHARTS/1.0"})
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", "replace")
    except Exception as exc:
        sys.exit(f"No se pudo acceder al chart mundial de Kworb/iTunes: {exc}")

    tracks = parse_chart(html)
    try:
        previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
        previous_tracks = previous.get("tracks", [])
    except (OSError, json.JSONDecodeError, AttributeError):
        previous_tracks = []
    if not tracks and previous_tracks:
        sys.exit("El chart no devolvió canciones de BABYMONSTER; se conservan los datos anteriores.")
    titles = [track["title"].casefold() for track in tracks]
    if len(titles) != len(set(titles)):
        sys.exit("El chart de iTunes devolvió títulos duplicados.")
    payload = {
        "artist": "BABYMONSTER",
        "platform": "iTunes Worldwide",
        "source": URL,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "note": "Solo canciones visibles en el chart mundial de iTunes de Kworb; puntos y puestos no son ventas ni un chart oficial de Apple.",
        "tracks": tracks
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Actualizadas {len(tracks)} canciones de BABYMONSTER en el chart mundial iTunes.")


if __name__ == "__main__":
    main()
