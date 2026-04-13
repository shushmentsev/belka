from typing import AsyncIterator

import pytest_asyncio
from sqlalchemy import Integer, String
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import Mapped, mapped_column

from belka.core.repository import SQLAlchemyRepository
from belka.core.schemas import SchemaModel
from belka.core.specification import Specification
from belka.infrastructure.database.base import Base


class Item(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), default="")
    value: Mapped[int] = mapped_column(Integer, default=0)
    category: Mapped[str] = mapped_column(String(50), default="default")

    def to_schema(self) -> "ItemSchema":
        return ItemSchema.model_validate(self)


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    title: Mapped[str] = mapped_column(String(50), default="")

    def to_dict(self) -> dict:
        return {"id": self.id, "title": self.title}


class ItemSchema(SchemaModel):
    id: int
    name: str
    value: int
    category: str


class ItemAggSchema(SchemaModel):
    category: str
    total: int


class ItemCountSchema(SchemaModel):
    total: int


class ItemValueGteSpec(Specification):
    def __init__(self, threshold: int) -> None:
        self._models_for_join = []
        self._models_for_outerjoin = []
        self._models_for_join_onclause = []
        self._filter = Item.value >= threshold


class ItemRepository(SQLAlchemyRepository[ItemSchema]):
    _model = Item


class TagRepository(SQLAlchemyRepository[dict]):
    _model = Tag


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncIterator[AsyncEngine]:
    eng = create_async_engine("sqlite+aiosqlite:///:memory:", future=True)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        yield eng
    finally:
        await eng.dispose()


@pytest_asyncio.fixture
async def session(engine: AsyncEngine) -> AsyncIterator[AsyncSession]:
    sm = async_sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)
    async with sm() as s:
        try:
            yield s
        finally:
            await s.rollback()


@pytest_asyncio.fixture
async def item_repo(session: AsyncSession) -> ItemRepository:
    return ItemRepository(session)


@pytest_asyncio.fixture
async def tag_repo(session: AsyncSession) -> TagRepository:
    return TagRepository(session)
