import uuid
from typing import Generic, TypeVar

from fastapi_users import BaseUserManager, UUIDIDMixin
from fastapi_users.password import PasswordHelperProtocol
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase

UserT = TypeVar("UserT")


class BaseAuthUserManager(
    UUIDIDMixin,
    BaseUserManager[UserT, uuid.UUID],
    Generic[UserT],
):
    """Базовый UserManager для belka.auth.

    Приложение наследует этот класс и переопределяет хуки
    (on_after_register, on_after_login и т. д.) под свою логику.
    Секреты для сброса/верификации передаются через конструктор,
    чтобы не хранить их в атрибутах класса.
    """

    def __init__(
        self,
        user_db: SQLAlchemyUserDatabase[UserT, uuid.UUID],
        password_helper: PasswordHelperProtocol | None = None,
        *,
        reset_password_token_secret: str,
        verification_token_secret: str,
    ) -> None:
        super().__init__(user_db, password_helper)
        self.reset_password_token_secret = reset_password_token_secret
        self.verification_token_secret = verification_token_secret


__all__ = ["BaseAuthUserManager"]
