#!/usr/bin/env python3
"""Guarda capturas históricas verificables sin inventar ceros para fuentes ausentes."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SPOTIFY_FILE = ROOT / "data" / "spotify-songs.json"
YOUTUBE_FILE = ROOT / "data" / "youtube-charts.json"
HISTORY_FILE = ROOT / "data" / "history.json"
MAX_DAYS = 365


def load_json(path, fallback):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return fallback


def num(value):
    try:
        return max(0, int(float(value or 0)))
    except (TypeError, ValueError):
        return 0


def main():
    now = datetime.now(timezone.utc)
    day = now.strftime("%Y-%m-%d")
    spotify = load_json(SPOTIFY_FILE, {})
    youtube = load_json(YOUTUBE_FILE, {})
    songs = spotify.get("tracks", [])
    videos = youtube.get("tracks", [])

    if not isinstance(songs, list):
        songs = []
    if not isinstance(videos, list):
        videos = []

    if not songs and not videos:
        sys.exit("No hay canciones ni videos disponibles; se omite la captura para no registrar datos vacíos como cero.")

    snapshot = {
        "date": day,
        "captured_at": now.isoformat(),
        "spotify": {
            "updated_at": spotify.get("updated_at"),
            "track_count": len(songs),
            "daily_streams": sum(num(track.get("daily")) for track in songs if isinstance(track, dict)) if songs else None,
            "total_streams": sum(num(track.get("streams")) for track in songs if isinstance(track, dict)) if songs else None,
            "top_tracks": [
                {"title": track.get("title", "Sin título"), "daily": num(track.get("daily")), "streams": num(track.get("streams"))}
                for track in sorted((t for t in songs if isinstance(t, dict)), key=lambda t: num(t.get("daily")), reverse=True)[:50]
            ]
        },
        "youtube": {
            "updated_at": youtube.get("updated_at"),
            "video_count": len(videos),
            "total_views": sum(num(video.get("views")) for video in videos if isinstance(video, dict)) if videos else None,
            "top_videos": [
                {"id": video.get("id", ""), "title": video.get("title", "Sin título"), "views": num(video.get("views")), "url": video.get("url", "")}
                for video in sorted((v for v in videos if isinstance(v, dict)), key=lambda v: num(v.get("views")), reverse=True)[:50]
            ]
        }
    }

    history = load_json(HISTORY_FILE, [])
    if not isinstance(history, list):
        history = []
    history = [item for item in history if isinstance(item, dict) and item.get("date") != day]
    history.append(snapshot)
    history.sort(key=lambda item: item.get("date", ""))
    history = history[-MAX_DAYS:]

    HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
    HISTORY_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Historial central actualizado: {day}; {len(history)} fechas conservadas.")


if __name__ == "__main__":
    main()
