#!/usr/bin/env python3
"""Validación ligera de los datos que publica el dashboard."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FILES = {
    "spotify": ROOT / "data" / "spotify-songs.json",
    "youtube": ROOT / "data" / "youtube-charts.json",
    "history": ROOT / "data" / "history.json",
}


def read_json(name, path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        sys.exit(f"{name}: JSON no válido o inaccesible: {exc}")


def nonnegative(value, context):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value < 0:
        sys.exit(f"{context}: se esperaba un número no negativo.")


def main():
    spotify = read_json("Spotify", FILES["spotify"])
    youtube = read_json("YouTube", FILES["youtube"])
    history = read_json("Historial", FILES["history"])

    if not isinstance(spotify, dict) or not isinstance(spotify.get("tracks"), list) or not spotify["tracks"]:
        sys.exit("Spotify: se requiere una lista de canciones no vacía.")
    for index, track in enumerate(spotify["tracks"]):
        if not isinstance(track, dict) or not isinstance(track.get("title"), str) or not track["title"].strip():
            sys.exit(f"Spotify: título ausente en la fila {index + 1}.")
        for key in ("streams", "daily"):
            nonnegative(track.get(key), f"Spotify fila {index + 1}, {key}")

    if not isinstance(youtube, dict) or not isinstance(youtube.get("tracks"), list):
        sys.exit("YouTube: se requiere un arreglo tracks, aunque pueda estar vacío.")
    for index, video in enumerate(youtube["tracks"]):
        if not isinstance(video, dict) or not isinstance(video.get("title"), str) or not video["title"].strip():
            sys.exit(f"YouTube: título ausente en la fila {index + 1}.")
        nonnegative(video.get("views"), f"YouTube fila {index + 1}, views")
        if video.get("url") and not str(video["url"]).startswith("https://www.youtube.com/watch?v="):
            sys.exit(f"YouTube fila {index + 1}: URL de video inesperada.")

    if not isinstance(history, list):
        sys.exit("Historial: se esperaba un arreglo JSON.")
    if len(history) > 365:
        sys.exit("Historial: supera el máximo de 365 capturas.")
    dates = [entry.get("date") for entry in history if isinstance(entry, dict)]
    if len(dates) != len(history) or len(set(dates)) != len(dates):
        sys.exit("Historial: registros inválidos o fechas duplicadas.")
    print(f"Validación correcta: {len(spotify['tracks'])} canciones, {len(youtube['tracks'])} videos, {len(history)} capturas históricas.")


if __name__ == "__main__":
    main()
