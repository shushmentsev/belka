from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from belka.core.schemas import SchemaModel


class Base(AsyncAttrs, DeclarativeBase):
    id: None
    __mapper_args__ = {"eager_defaults": True}

    def to_dict(self) -> dict:
        raise NotImplementedError

    def to_schema(self) -> SchemaModel:
        raise NotImplementedError
