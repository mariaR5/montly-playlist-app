import uuid
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services import playlist_service
from app.api.schemas.playlist import (
    CreatePlaylistRequest, UpdatePlaylistRequest,
    AddSongRequest, PlaylistResponse, PlaylistSummary
)

router = APIRouter(prefix="/playlists", tags=["playlists"])


@router.post("", response_model=PlaylistResponse, status_code=201)
async def create_playlist(
    data: CreatePlaylistRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await playlist_service.create_playlist(data, current_user, db)


@router.get("/archive", response_model=list[PlaylistSummary])
async def get_archive(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await playlist_service.get_user_archive(current_user, db)


@router.get("/{playlist_id}", response_model=PlaylistResponse)
async def get_playlist(
    playlist_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await playlist_service.get_playlist_by_id(playlist_id, current_user, db)


@router.patch("/{playlist_id}", response_model=PlaylistResponse)
async def update_playlist(
    playlist_id: uuid.UUID,
    data: UpdatePlaylistRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await playlist_service.update_playlist(playlist_id, data, current_user, db)


@router.post("/{playlist_id}/songs", response_model=PlaylistResponse)
async def add_song(
    playlist_id: uuid.UUID,
    data: AddSongRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await playlist_service.add_song(playlist_id, data, current_user, db)


@router.delete("/{playlist_id}/songs/{song_id}", response_model=PlaylistResponse)
async def remove_song(
    playlist_id: uuid.UUID,
    song_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await playlist_service.remove_song(playlist_id, song_id, current_user, db)


@router.get("", response_model=PlaylistResponse)
async def get_monthly_playlist(
    month: int = Query(..., ge=1, le=12),
    year: int = Query(..., ge=2020),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await playlist_service.get_user_playlist(month, year, current_user, db)