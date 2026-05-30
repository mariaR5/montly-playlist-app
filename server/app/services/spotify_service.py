from annotated_types import T
import base64
import httpx
from app.core.redis import get_redis
from app.core.config import settings

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"
SPOTIFY_BASE_URL = "https://api.spotify.com/v1"
TOKEN_CACHE_KEY = "spotify:access_token"

async def _get_access_token() -> str:
    redis = await get_redis()

    cached_token = await redis.get(TOKEN_CACHE_KEY)
    if cached_token:
        return cached_token

    credentials = f"{settings.SPOTIFY_CLIENT_ID}:{settings.SPOTIFY_CLIENT_SECRET}"
    encoded = base64.b64encode(credentials.encode()).decode()

    async with httpx.AsyncClient() as client:
        response = await client.post(
            SPOTIFY_TOKEN_URL,
            headers={
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/x-www-form-urlencoded"
            },
            data={
                "grant_type": "client_credentials"
            }
        )
        response.raise_for_status()
        token_data = response.json()
    
    token = token_data["access_token"]
    expires_in = token_data["expires_in"]

    await redis.setex(TOKEN_CACHE_KEY, expires_in-60, token)
    return token


async def search_tracks(query: str, limit: int = 10) -> list[dict]:
    token = await _get_access_token()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_BASE_URL}/search",
            headers={
                "Authorization": f"Bearer {token}"
            },
            params={
                "q": query,
                "type": "track",
                "limit": limit,
                "market": "IN"
            }
        )

        response.raise_for_status()
        data = response.json()
    
    tracks = data["tracks"]["items"]
    return [_shape_track(track) for track in tracks]


async def get_track(spotify_id: str) -> dict | None:
    token = await _get_access_token()

    async with httpx.AsyncClient() as client:
        response = await client.get(
            f"{SPOTIFY_BASE_URL}/tracks/{spotify_id}",
            headers={
                "Authorization": f"Bearer {token}"
            }
        )
        if response.status_code == 404:
            return None
        response.raise_for_status()
        track_data = response.json()

    return _shape_track(track_data)


def _shape_track(track: dict) -> dict:
    album = track.get("album", {})
    artists = track.get("artists", {})
    images = album.get("images", {})

    return {
        "spotify_id": track["id"],
        "title": track["name"],
        "artist": ", ".join(a["name"] for a in artists),
        "album": album.get("name"),
        "album_art_url": images[0]["url"] if images else None,
        "duration_ms": track.get("duration_ms"),
        "preview_url": track.get("preview_url"),
        "spotify_url": track.get("external_urls", {}).get("spotify"),
    }