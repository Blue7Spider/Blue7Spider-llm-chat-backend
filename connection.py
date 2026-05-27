from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app import settings

# Aszinkron DB motor inicializálása
async_engine = create_async_engine(
    settings.database_url,
    echo=False,
    future=True
)

# Szálbiztos, aszinkron session gyár
async_session_factory = async_sessionmaker(
    bind=async_engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False
)

Base = declarative_base()

# Dependencia az API végpontok számára
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        try:
            yield session
        finally:
            await session.close()