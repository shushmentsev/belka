from collections.abc import AsyncIterator
from dataclasses import dataclass

from dishka import Provider, Scope, provide
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from belka.infrastructure.database.database import create_session_maker


@dataclass(frozen=True, slots=True)
class DatabaseConfig:
    dsn: str


class DatabaseProvider(Provider):
    @provide(scope=Scope.APP)
    def session_maker(
        self,
        config: DatabaseConfig,
    ) -> async_sessionmaker[AsyncSession]:
        return create_session_maker(config.dsn)

    @provide(scope=Scope.REQUEST)
    async def session(
        self,
        session_maker: async_sessionmaker[AsyncSession],
    ) -> AsyncIterator[AsyncSession]:
        async with session_maker() as session:
            yield session
