import re

from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, declared_attr

from belka.core.schemas import SchemaModel


def _camel_to_snake(name: str) -> str:
    s1 = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", name)
    return re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", s1).lower()


class Base(AsyncAttrs, DeclarativeBase):
    id: None
    __mapper_args__ = {"eager_defaults": True}

    # noinspection PyMethodParameters
    @declared_attr.directive
    def __tablename__(cls) -> str:
        return _camel_to_snake(cls.__name__)

    def to_dict(self) -> dict:
        raise NotImplementedError

    def to_schema(self) -> SchemaModel:
        raise NotImplementedError


if __name__ == "__main__":
    original_name_1 = "User"
    original_name_2 = "RoleRelationUser"

    result_name_1 = _camel_to_snake(original_name_1)
    result_name_2 = _camel_to_snake(original_name_2)

    print(f"{result_name_1=}")
    print(f"{result_name_2=}")
