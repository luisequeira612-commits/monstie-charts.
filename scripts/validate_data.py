#!/usr/bin/env python3
"""Validación estricta de los datos que publica el dashboard."""
import json
import math
import re
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "spotify": ROOT / "data" / "spotify-songs.json",
    "youtube": ROOT / "data" / "youtube-charts.json",
    "history": ROOT / "data" / "history.json",
}
YOUTUBE_URL = re.compile(r"^https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}$")


def fail(message):
    sys.exit(message)


def read_json(name, path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{name}: JSON no válido o inaccesible: {exc}")


def nonnegative(value, context):
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        fail(f"{context}: se esperaba un número finito no negativo.")


def valid_date(value, context):
    if not isinstance(value, str):
        fail(f"{context}: falta una fecha ISO 8601 (AAAA-MM-DD).")
    try:
        parsed = date.fromisoformat(value)
    except ValueError:
        fail(f"{context}: fecha inválida {value!r}; se esperaba AAAA-MM-DD.")
    if parsed.isoformat() != value:
        fail(f"{context}: fecha no canónica {value!r}.")


def validate_history(history):
    if not isinstance(history, list):
        fail("Historial: se esperaba un arreglo JSON.")
    if len(history) > 365:
        fail("Historial: supera el máximo de 365 capturas.")

    dates = []
    for index, entry in enumerate(history, start=1):
        context = f"Historial fila {index}"
        if not isinstance(entry, dict):
            fail(f"{context}: se esperaba un objeto.")
        valid_date(entry.get("date"), context)
        dates.append(entry["date"])
        for platform in ("spotify", "youtube"):
            section = entry.get(platform)
            if not isinstance(section, dict):
                fail(f"{context}: falta el objeto {platform}.")
            for key in ("daily_streams", "total_streams", "total_views"):
                if key in section and section[key] is not None:
                    nonnegative(section[key], f"{context}, {platform}.{key}")
            for key in ("track_count", "video_count"):
                if key in section:
                    nonnegative(section[key], f"{context}, {platform}.{key}")

    if len(set(dates)) != len(dates):
        fail("Historial: hay fechas duplicadas.")
    if dates != sorted(dates):
        fail("Historial: las capturas deben estar ordenadas por fecha ascendente.")


def main():
    spotify = read_json("Spotify", FILES["spotify"])
    youtube = read_json("YouTube", FILES["youtube"])
    history = read_json("Historial", FILES["history"])

    if not isinstance(spotify, dict) or not isinstance(spotify.get("tracks"), list) or not spotify["tracks"]:
        fail("Spotify: se requiere una lista de canciones no vacía.")
    for index, track in enumerate(spotify["tracks"], start=1):
        if not isinstance(track, dict) or not isinstance(track.get("title"), str) or not track["title"].strip():
            fail(f"Spotify: título ausente en la fila {index}.")
        for key in ("streams", "daily"):
            nonnegative(track.get(key), f"Spotify fila {index}, {key}")

    if not isinstance(youtube, dict) or not isinstance(youtube.get("tracks"), list):
        fail("YouTube: se requiere un arreglo tracks, aunque pueda estar vacío.")
    for index, video in enumerate(youtube["tracks"], start=1):
        if not isinstance(video, dict) or not isinstance(video.get("title"), str) or not video["title"].strip():
            fail(f"YouTube: título ausente en la fila {index}.")
        nonnegative(video.get("views"), f"YouTube fila {index}, views")
        url = video.get("url")
        if url and (not isinstance(url, str) or not YOUTUBE_URL.fullmatch(url)):
            fail(f"YouTube fila {index}: URL de video inesperada o ID inválido.")

    validate_history(history)
    print(
        f"Validación correcta: {len(spotify['tracks'])} canciones, "
        f"{len(youtube['tracks'])} videos, {len(history)} capturas históricas."
    )


if __name__ == "__main__":
    main()
