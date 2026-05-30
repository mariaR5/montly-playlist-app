from fastapi import APIRouter, Depends, Query, HTTPException
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services import spotify_service
from app.api.schemas.spotify import SearchResponse, TrackResult

router = APIRouter(prefix="/search", tags=["search"])

@router.get("", response_model=SearchResponse)
async def search_tracks(
    q: str = Query(..., min_length=1, max_length=100, description="Search query"),
    limit: int = Query(default=10, ge=1, le=20),
    current_user: User = Depends(get_current_user)
):
    if not q.strip():
        raise HTTPException(status_code=400, detail="Search query cannot be empty")
    
    tracks = await spotify_service.search_tracks(q.strip(), limit=limit)

    return SearchResponse(
        query=q,
        results=[TrackResult(**t) for t in tracks],
        count=len(tracks)
    )


@router.get("/track/{spotify_id}", response_model=TrackResult)
async def get_track(
    spotify_id: str,
    current_user: User = Depends(get_current_user)
):
    track = await spotify_service.get_track(spotify_id)

    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    return TrackResult(**track)