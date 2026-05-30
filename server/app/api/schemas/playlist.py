from pydantic import BaseModel, field_validator
from datetime import datetime
from uuid import UUID

class AddSongRequest(BaseModel):
    spotify_track_id: str
    title: str
    artist: str
    album: str | None = None
    album_art_url: str | None = None
    duration_ms: int | None = None
    preview_url: str | None = None
    spotify_url: str | None = None
    position: int | None = None  # if None, appends to end

class CreatePlaylistRequest(BaseModel):
    month: int
    year: int
    title: str | None = None
    template_id: UUID | None = None

    @field_validator("month")
    @classmethod
    def month_valid(cls, v):
        if not 1 <= v <= 12:
            raise ValueError("Month must be between 1 and 12")
        return v

    @field_validator("year")
    @classmethod
    def year_valid(cls, v):
        if not 2020 <= v <= 2100:
            raise ValueError("Invalid year")
        return v

class UpdatePlaylistRequest(BaseModel):
    title: str | None = None
    template_id: UUID | None = None
    mood_label: str | None = None
    ai_caption: str | None = None

class SongResponse(BaseModel):
    id: UUID
    spotify_track_id: str
    title: str
    artist: str
    album: str | None
    album_art_url: str | None
    duration_ms: int | None
    preview_url: str | None
    spotify_url: str | None
    position: int
    added_at: datetime

    class Config:
        from_attributes = True

class PlaylistResponse(BaseModel):
    id: UUID
    month: int
    year: int
    title: str | None
    mood_label: str | None
    ai_caption: str | None
    image_url: str | None
    template_id: UUID | None
    is_published: bool
    songs: list[SongResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class PlaylistSummary(BaseModel):
    """Lighter version for archive listing - no songs list"""
    id: UUID
    month: int
    year: int
    title: str | None
    mood_label: str | None
    image_url: str | None
    is_published: bool
    song_count: int
    created_at: datetime

    class Config:
        from_attributes = True