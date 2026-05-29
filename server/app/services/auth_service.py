from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.schemas.auth import RegisterRequest, TokenResponse, LoginRequest
from app.core.security import create_access_token, verify_password, hash_password
from app.models.user import User

async def register_user(data: RegisterRequest, db: AsyncSession) -> TokenResponse:
    # Check email already taken
    result = await db.execute(select(User).where(User.email == data.email))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email is already registered"
        )

    # Check username already taken
    result = await db.execute(select(User).where(User.username == data.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this username is already registered"
        )
    
    user = User(
        email=data.email,
        username=data.username,
        hashed_password=hash_password(data.password),
    )

    db.add(user)
    await db.flush()

    token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        username=user.username,
        email=user.email
    )


async def login_user(data: LoginRequest, db: AsyncSession) -> TokenResponse:
    result = await db.execute(select(User).where(User.email == data.email))
    user = result.scalar_one_or_none()

    if not user or not verify_password(data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token(subject=str(user.id))

    return TokenResponse(
        access_token=token,
        user_id=str(user.id),
        username=user.username,
        email=user.email
    )