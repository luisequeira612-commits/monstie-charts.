import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

API_KEY = os.environ.get("YOUTUBE_API_KEY")
BASE_URL = "https://www.googleapis.com/youtube/v3"
CHANNEL_HANDLE = "@BABYMONSTER"
ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "data" / "youtube-charts.json"

# Evita clasificar teasers, making films y clips promocionales como videoclips oficiales.
EXCLUDE_TERMS = (
    "teaser", "making film", "highlight clip", "out now", "hits ",
    "behind", "magazine", "reaction", "dance practice", "performance video"
)
INCLUDE_TERMS = ("m/v", " mv", "music video", "official video")


def api_get(endpoint, params):
    request_params = dict(params)
    request_params["key"] = API_KEY
    url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(request_params)}"
    with urllib.request.urlopen(url, timeout=30) as response:
        payload = json.load(response)
    if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
        raise RuntimeError(f"YouTube API devolvió una respuesta inesperada para {endpoint}.")
    return payload


def validate_tracks(tracks, candidates_count, previous_count=0):
    """Keep empty or truncated API responses from erasing a usable chart."""
    if candidates_count == 0:
        raise RuntimeError(
            "No se detectaron videoclips con los filtros actuales; se conservan los datos anteriores."
        )
    if not tracks:
        raise RuntimeError(
            "YouTube no devolvió estadísticas para los videos candidatos; se conservan los datos anteriores."
        )
    ids = [track.get("id") for track in tracks]
    if any(not isinstance(video_id, str) or not video_id for video_id in ids):
        raise RuntimeError("YouTube devolvió un ID de video inválido.")
    if len(ids) != len(set(ids)):
        raise RuntimeError("YouTube devolvió videos duplicados; se rechaza la actualización.")
    if previous_count >= 4 and len(tracks) < max(2, previous_count // 2):
        raise RuntimeError(
            f"Respuesta sospechosamente corta de YouTube ({len(tracks)} videos frente a "
            f"{previous_count} anteriores); se conservan los datos anteriores."
        )
    for track in tracks:
        views = track.get("views")
        if isinstance(views, bool) or not isinstance(views, int) or views < 0:
            raise RuntimeError("YouTube devolvió un contador de vistas inválido.")
    return tracks


def previous_count():
    try:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        tracks = data.get("tracks", [])
        return len(tracks) if isinstance(tracks, list) else 0
    except (OSError, json.JSONDecodeError, AttributeError):
        return 0


def validate_tracks(tracks, candidates_count, previous_count=0):
    """Reject empty, duplicated, or suspiciously incomplete API responses."""
    if candidates_count == 0:
        raise RuntimeError("No se detectaron videoclips; se conservan los datos anteriores.")
    if not tracks:
        raise RuntimeError("YouTube no devolvió estadísticas; se conservan los datos anteriores.")
    ids = [track.get("id") for track in tracks]
    if any(not isinstance(video_id, str) or not video_id for video_id in ids):
        raise RuntimeError("YouTube devolvió un ID de video inválido.")
    if len(ids) != len(set(ids)):
        raise RuntimeError("YouTube devolvió videos duplicados.")
    if previous_count >= 4 and len(tracks) < max(2, previous_count // 2):
        raise RuntimeError("Respuesta sospechosamente corta de YouTube; se conservan los datos anteriores.")
    for track in tracks:
        views = track.get("views")
        if isinstance(views, bool) or not isinstance(views, int) or views < 0:
            raise RuntimeError("YouTube devolvió un contador de vistas inválido.")
    return tracks


def previous_count():
    try:
        data = json.loads(OUTPUT.read_text(encoding="utf-8"))
        tracks = data.get("tracks", [])
        return len(tracks) if isinstance(tracks, list) else 0
    except (OSError, json.JSONDecodeError, AttributeError):
        return 0


def main():
    if not API_KEY:
        print("YOUTUBE_API_KEY no configurada; se conservan los datos existentes.")
        return

    channel_data = api_get("channels", {
        "part": "contentDetails",
        "forHandle": CHANNEL_HANDLE
    })
    channels = channel_data["items"]
    if not channels or not isinstance(channels[0], dict):
        raise RuntimeError("No se encontró el canal oficial; comprueba @BABYMONSTER.")

    try:
        uploads_id = channels[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    except (KeyError, TypeError):
        raise RuntimeError("La respuesta del canal no contiene la lista de subidas esperada.")

    videos = []
    page_token = None

    for _ in range(5):
        params = {"part": "snippet,contentDetails", "playlistId": uploads_id, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        page = api_get("playlistItems", params)
        videos.extend(page["items"])
        page_token = page.get("nextPageToken")
        if not page_token:
            break

    candidates = []
    seen_ids = set()
    for item in videos:
        if not isinstance(item, dict):
            continue
        snippet = item.get("snippet", {})
        if not isinstance(snippet, dict):
            continue
        title = snippet.get("title", "")
        normalized = title.casefold() if isinstance(title, str) else ""
        if any(term in normalized for term in EXCLUDE_TERMS):
            continue
        if not any(term in normalized for term in INCLUDE_TERMS):
            continue
        video_id = item.get("contentDetails", {}).get("videoId")
        if video_id and video_id not in seen_ids:
            candidates.append({"id": video_id, "title": title})
            seen_ids.add(video_id)

    if not candidates:
        raise RuntimeError(
            "No se detectaron videoclips oficiales; no se reemplazan los datos existentes."
        )

    tracks = []
    for start in range(0, len(candidates), 50):
        batch = candidates[start:start + 50]
        stats = api_get("videos", {
            "part": "statistics,snippet",
            "id": ",".join(video["id"] for video in batch)
        })
        for video in stats["items"]:
            if not isinstance(video, dict) or not isinstance(video.get("snippet"), dict):
                raise RuntimeError("YouTube devolvió un registro de video incompleto.")
            try:
                views = int(video.get("statistics", {})["viewCount"])
                video_id = video["id"]
                title = video["snippet"]["title"]
            except (KeyError, TypeError, ValueError):
                raise RuntimeError("YouTube devolvió estadísticas incompletas; se conserva el chart anterior.")
            tracks.append({
                "id": video_id,
                "title": title,
                "views": views,
                "url": f"https://www.youtube.com/watch?v={video_id}",
                "published_at": video["snippet"].get("publishedAt", "")
            })

    validate_tracks(tracks, len(candidates), previous_count())
    tracks.sort(key=lambda video: video["views"], reverse=True)
    data = {
        "tracks": tracks,
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "note": (
            "Vistas públicas de videoclips detectados en el canal oficial. "
            "Se excluyen teasers y material promocional cuando el título lo permite."
        )
    }
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Actualizados {len(tracks)} videoclips de YouTube.")


if __name__ == "__main__":
    main()
