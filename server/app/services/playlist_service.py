import uuid

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.schemas.playlist import (
    AddSongRequest,
    CreatePlaylistRequest,
    PlaylistResponse,
    PlaylistSummary,
    SongResponse,
    UpdatePlaylistRequest,
)
from app.models.playlist import Playlist, PlaylistSong
from app.models.template import Template
from app.models.user import User


async def create_playlist(
    data: CreatePlaylistRequest,
    current_user: User,
    db: AsyncSession
) -> PlaylistResponse:

    existing = await db.execute(
        select(Playlist).where(
            and_(
                Playlist.user_id == current_user.id,
                Playlist.month == data.month,
                Playlist.year == data.year
            )

        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You already have playlist for {data.month}/{data.year}"
        )

    if data.template_id:
        # Check if template exists
        template_result = await db.execute(
            select(Template).where(Template.id == data.template_id)
        )
        if not template_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified template does not exist"
            )
    
    playlist = Playlist(
        user_id=current_user.id,
        month=data.month,
        year=data.year,
        title=data.title,
        template_id=data.template_id
    )

    db.add(playlist)
    await db.flush()

    return await _get_playlist_full(playlist.id, db)

async def get_user_playlist(
    month: int,
    year: int,
    current_user: User,
    db: AsyncSession
) -> PlaylistResponse:
    
    playlist = await db.execute(
        select(Playlist)
        .where(
            and_(
                Playlist.user_id == current_user.id,
                Playlist.month == month,
                Playlist.year == year
            )
        )
        .options(selectinload(Playlist.songs))
    )

    playlist = playlist.scalar_one_or_none()

    if not playlist:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No playlist found for {month}/{year}"
        )

    return _to_response(playlist)

async def get_user_archive(
    current_user: User,
    db: AsyncSession
) -> list[PlaylistSummary]:
    result = await db.execute(
        select(
            Playlist,
            func.count(PlaylistSong.id).label("song_count")
        )
        .outerjoin(PlaylistSong, PlaylistSong.playlist_id == Playlist.id)
        .where(Playlist.user_id == current_user.id)
        .group_by(Playlist.id)
        .order_by(Playlist.year.desc(), Playlist.month.desc())
    )
    rows = result.all()

    return [
        PlaylistSummary(
            id=playlist.id,
            month=playlist.month,
            year=playlist.year,
            title=playlist.title,
            mood_label=playlist.mood_label,
            image_url=playlist.image_url,
            is_published=playlist.is_published,
            song_count=song_count,
            created_at=playlist.created_at
        )
        for playlist, song_count in rows
    ]

async def get_playlist_by_id(
    playlist_id: uuid.UUID,
    current_user: User,
    db: AsyncSession
) -> PlaylistResponse:
    await _get_owned_playlist(playlist_id, current_user, db)
    return await _get_playlist_full(playlist_id, db)

async def add_song(
    playlist_id: uuid.UUID,
    data: AddSongRequest,
    current_user: User,
    db: AsyncSession
) -> PlaylistResponse:
    playlist = await _get_owned_playlist(playlist_id, current_user, db)

    # Get current max position
    max_pos_result = await db.execute(
        select(func.max(PlaylistSong.position)).where(
            PlaylistSong.playlist_id == playlist_id
        )
    )
    max_position = max_pos_result.scalar() or 0

    # Check song not already in playlist
    duplicate = await db.execute(
        select(PlaylistSong).where(
            and_(
                PlaylistSong.playlist_id == playlist_id,
                PlaylistSong.spotify_track_id == data.spotify_track_id
            )
        )
    )
    if duplicate.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This song is already in the playlist"
        )

    song = PlaylistSong(
        playlist_id=playlist_id,
        spotify_track_id=data.spotify_track_id,
        title=data.title,
        artist=data.artist,
        album=data.album,
        album_art_url=data.album_art_url,
        duration_ms=data.duration_ms,
        preview_url=data.preview_url,
        spotify_url=data.spotify_url,
        position=data.position if data.position is not None else max_position + 1
    )
    db.add(song)
    await db.flush()

    return await _get_playlist_full(playlist_id, db)


async def remove_song(
    playlist_id: uuid.UUID,
    song_id: uuid.UUID,
    current_user: User,
    db: AsyncSession
) -> PlaylistResponse:
    await _get_owned_playlist(playlist_id, current_user, db)

    result = await db.execute(
        select(PlaylistSong).where(
            and_(
                PlaylistSong.id == song_id,
                PlaylistSong.playlist_id == playlist_id
            )
        )
    )
    song = result.scalar_one_or_none()
    if not song:
        raise HTTPException(status_code=404, detail="Song not found in this playlist")

    await db.delete(song)
    await db.flush()

    return await _get_playlist_full(playlist_id, db)


async def update_playlist(
    playlist_id: uuid.UUID,
    data: UpdatePlaylistRequest,
    current_user: User,
    db: AsyncSession
) -> PlaylistResponse:
    playlist = await _get_owned_playlist(playlist_id, current_user, db)

    if data.title is not None:
        playlist.title = data.title
    if data.template_id is not None:
        # Check if template exists
        template_result = await db.execute(
            select(Template).where(Template.id == data.template_id)
        )
        if not template_result.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Specified template does not exist"
            )
        playlist.template_id = data.template_id
    if data.mood_label is not None:
        playlist.mood_label = data.mood_label
    if data.ai_caption is not None:
        playlist.ai_caption = data.ai_caption

    await db.flush()
    return await _get_playlist_full(playlist_id, db)


async def _get_owned_playlist(
    playlist_id: uuid.UUID,
    current_user: User,
    db: AsyncSession
) -> Playlist:
    """Fetch a playlist and verify ownership. Raises 404 or 403 if not accessible."""
    result = await db.execute(
        select(Playlist).where(Playlist.id == playlist_id)
    )
    playlist = result.scalar_one_or_none()

    if not playlist:
        raise HTTPException(status_code=404, detail="Playlist not found")

    if playlist.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this playlist"
        )

    return playlist


async def _get_playlist_full(
    playlist_id: uuid.UUID,
    db: AsyncSession
) -> PlaylistResponse:
    """Load a playlist with all songs eagerly loaded."""
    result = await db.execute(
        select(Playlist)
        .where(Playlist.id == playlist_id)
        .options(selectinload(Playlist.songs))
    )
    playlist = result.scalar_one()
    return _to_response(playlist)


def _to_response(playlist: Playlist) -> PlaylistResponse:
    return PlaylistResponse(
        id=playlist.id,
        month=playlist.month,
        year=playlist.year,
        title=playlist.title,
        mood_label=playlist.mood_label,
        ai_caption=playlist.ai_caption,
        image_url=playlist.image_url,
        template_id=playlist.template_id,
        is_published=playlist.is_published,
        songs=[SongResponse.model_validate(s) for s in playlist.songs],
        created_at=playlist.created_at,
        updated_at=playlist.updated_at
    )
