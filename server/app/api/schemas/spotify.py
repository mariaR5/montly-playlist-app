from pydantic import BaseModel

class TrackResult(BaseModel):
    spotify_id: str
    title: str
    artist: str
    album: str | None
    album_art_url: str | None
    duration_ms: int | None
    preview_url: str | None
    spotify_url: str | None

class SearchResponse(BaseModel):
    query: str
    results: list[TrackResult]
    count: int