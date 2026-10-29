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
    params["key"] = API_KEY
    url = f"{BASE_URL}/{endpoint}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=30) as response:
        return json.load(response)


def main():
    if not API_KEY:
        print("YOUTUBE_API_KEY no configurada; se conservan los datos existentes.")
        return

    channel_data = api_get("channels", {
        "part": "contentDetails",
        "forHandle": CHANNEL_HANDLE
    })
    channels = channel_data.get("items", [])
    if not channels:
        raise RuntimeError("No se encontró el canal oficial; comprueba @BABYMONSTER.")

    uploads_id = channels[0]["contentDetails"]["relatedPlaylists"]["uploads"]
    videos = []
    page_token = None

    for _ in range(5):
        params = {"part": "snippet,contentDetails", "playlistId": uploads_id, "maxResults": 50}
        if page_token:
            params["pageToken"] = page_token
        page = api_get("playlistItems", params)
        videos.extend(page.get("items", []))
        page_token = page.get("nextPageToken")
        if not page_token:
            break

    candidates = []
    for item in videos:
        snippet = item.get("snippet", {})
        title = snippet.get("title", "")
        normalized = title.casefold()
        if any(term in normalized for term in EXCLUDE_TERMS):
            continue
        if not any(term in normalized for term in INCLUDE_TERMS):
            continue
        video_id = item.get("contentDetails", {}).get("videoId")
        if video_id:
            candidates.append({"id": video_id, "title": title})

    tracks = []
    for start in range(0, len(candidates), 50):
        batch = candidates[start:start + 50]
        stats = api_get("videos", {
            "part": "statistics,snippet",
            "id": ",".join(video["id"] for video in batch)
        })
        for video in stats.get("items", []):
            tracks.append({
                "id": video["id"],
                "title": video["snippet"]["title"],
                "views": int(video.get("statistics", {}).get("viewCount", 0)),
                "url": f"https://www.youtube.com/watch?v={video['id']}",
                "published_at": video["snippet"].get("publishedAt", "")
            })

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
