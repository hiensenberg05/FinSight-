import urllib.parse
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from backend.app.core.config import settings
from backend.app.db.base import Base


def get_normalized_db_url(raw_url: str) -> str:
    """Normalize database connection string for async SQLAlchemy (e.g. Render PostgreSQL)."""
    if not raw_url:
        return raw_url
    url = raw_url
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # Strip ?sslmode=... from asyncpg URLs since asyncpg handles SSL via connect_args
    if "sslmode=" in url:
        parsed = urllib.parse.urlparse(url)
        query = urllib.parse.parse_qs(parsed.query)
        query.pop("sslmode", None)
        new_query = urllib.parse.urlencode(query, doseq=True)
        url = urllib.parse.urlunparse(parsed._replace(query=new_query))
    return url


# Engine configuration
db_url = get_normalized_db_url(settings.DATABASE_URL)
connect_args = {}
if "sqlite" in db_url:
    connect_args["check_same_thread"] = False

engine = create_async_engine(
    db_url,
    echo=settings.DEBUG,
    connect_args=connect_args,
    future=True,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency that yields an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    async with engine.begin() as conn:
        # Import models so Base has metadata registered
        import backend.app.db.models  # noqa: F401
        await conn.run_sync(Base.metadata.create_all)
