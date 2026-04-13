from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)


def create_session_maker(url: str) -> async_sessionmaker[AsyncSession]:
    engine = create_async_engine(
        url,
        future=True,
        echo=False,
        pool_recycle=60 * 60 * 2,
        pool_pre_ping=True,
        pool_size=50,
        max_overflow=20,
    )
    return async_sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
