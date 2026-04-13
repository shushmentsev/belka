from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from belka.core.schemas import ApiModel

T = TypeVar("T")


class PaginationParams(BaseModel):
    page: int = Field(ge=1)
    per_page: int = Field(ge=1)


class PaginationResponse(ApiModel, Generic[T]):
    entities: list[T]
    entities_amount: int = Field(default=0, ge=0)
