import uuid

from fastapi_users import schemas


class BaseUserRead(schemas.BaseUser[uuid.UUID]):
    pass


class BaseUserCreate(schemas.BaseUserCreate):
    pass


class BaseUserUpdate(schemas.BaseUserUpdate):
    pass


__all__ = ["BaseUserCreate", "BaseUserRead", "BaseUserUpdate"]
