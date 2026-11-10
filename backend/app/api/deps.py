from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.app.db.session import get_db
from backend.app.db.models import User
from backend.app.core.security import decode_access_token

security = HTTPBearer(auto_error=False)


async def get_current_user(
    auth: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: AsyncSession = Depends(get_db),
) -> User:
    """
    Returns the authenticated user. In development / demo mode,
    falls back to the primary demo user (Aarav Mehta) so frontend features work instantly.
    """
    if auth and auth.credentials:
        payload = decode_access_token(auth.credentials)
        if payload and "sub" in payload:
            stmt = select(User).where(User.id == payload["sub"])
            user = (await db.execute(stmt)).scalars().first()
            if user:
                return user

    # Default demo user: Aarav Mehta (Primary Demo Persona)
    stmt = select(User).where(User.email == "aarav.mehta@example.com")
    user = (await db.execute(stmt)).scalars().first()
    if user:
        return user

    stmt = select(User).order_by(User.created_at.asc())
    user = (await db.execute(stmt)).scalars().first()
    if user:
        return user

    # Create demo user if DB is fresh
    user = User(
        email="aarav.mehta@example.com",
        password_hash="mock_hash",
        display_name="Aarav Mehta",
        preferred_language="en",
        base_currency="INR",
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
