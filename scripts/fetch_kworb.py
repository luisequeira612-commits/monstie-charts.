
#!/usr/bin/env python3
import json
import re
import sys
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

URL = "https://kworb.net/spotify/artist/1SIocsqdEefUTE6XKGUiVS_songs.html"
OUTPUT = Path("data/spotify-songs.json")


class TableParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tables = []
        self.table = None
        self.row = None
        self.cell = None
        self.active = False

    def handle_starttag(self, tag, attrs):
        if tag == "table":
            self.active = True
            self.table = []
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
            self.table = None
            self.active = False


def number(value):
    digits = re.sub(r"[^0-9]", "", value or "")
    return int(digits) if digits else 0


def validate_tracks(tracks, previous_count=0, previous_streams=0):
    """Reject empty, duplicate, or suspiciously truncated source responses."""
    if not tracks:
        raise RuntimeError("Kworb no devolvió canciones; se conservan los datos anteriores.")
    titles = [track["title"].strip().casefold() for track in tracks]
    if len(titles) != len(set(titles)):
        raise RuntimeError("Kworb devolvió títulos duplicados.")
    if previous_count >= 10 and len(tracks) < max(5, previous_count // 2):
        raise RuntimeError("Respuesta sospechosamente corta de Kworb; se conservan los datos anteriores.")
    if previous_streams > 0 and sum(track["streams"] for track in tracks) == 0:
        raise RuntimeError("Kworb devolvió cero streams totales; se conservan los datos anteriores.")
    return tracks


def previous_metrics():
    try:
        previous = json.loads(OUTPUT.read_text(encoding="utf-8"))
        tracks = previous.get("tracks", [])
        if not isinstance(tracks, list):
            return 0, 0
        return len(tracks), sum(
            t.get("streams", 0) for t in tracks if isinstance(t, dict)
            and isinstance(t.get("streams", 0), (int, float))
            and not isinstance(t.get("streams", 0), bool)
        )
    except (OSError, json.JSONDecodeError, AttributeError):
        return 0, 0


def main():
    request = urllib.request.Request(
        URL, headers={"User-Agent": "MONSTIE-CHARTS/1.0"}
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            html = response.read().decode("utf-8", "replace")
    except Exception as exc:
        sys.exit(f"No se pudo acceder a Kworb: {exc}")

    parser = TableParser()
    parser.feed(html)
    tracks = []

    for table in parser.tables:
        if not table:
            continue
        header = [cell.lower() for cell in table[0]]
        title_col = next(
            (i for i, value in enumerate(header) if "song title" in value), None
        )
        streams_col = next(
            (i for i, value in enumerate(header) if value == "streams"), None
        )
        daily_col = next(
            (i for i, value in enumerate(header) if value == "daily"), None
        )

        if None in (title_col, streams_col, daily_col):
            continue

        for row in table[1:]:
            if max(title_col, streams_col, daily_col) >= len(row):
                continue
            title = row[title_col].strip()
            if not title or title.lower() == "total":
                continue
            tracks.append({
                "title": title,
                "streams": number(row[streams_col]),
                "daily": number(row[daily_col]),
                "source": URL
            })
        if tracks:
            break

    old_count, old_streams = previous_metrics()
    try:
        validate_tracks(tracks, old_count, old_streams)
    except RuntimeError as exc:
        sys.exit(str(exc))

    payload = {
        "artist": "BABYMONSTER",
        "platform": "Spotify",
        "source": URL,
        "updated_at": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
        "note": "Streams reportados por Kworb; no son puestos oficiales del Top 200.",
        "tracks": tracks
    }

    OUTPUT.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8"
    )
    print(f"Actualizadas {len(tracks)} canciones.")


if __name__ == "__main__":
    main()
          
