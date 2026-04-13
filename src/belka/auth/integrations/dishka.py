import uuid
from collections.abc import Callable
from typing import TypeVar

from dishka import Provider, Scope, provide
from fastapi_users.authentication import AuthenticationBackend
from fastapi_users_db_sqlalchemy import SQLAlchemyUserDatabase
from sqlalchemy.ext.asyncio import AsyncSession

from belka.auth.backends import make_cookie_backend
from belka.auth.config import AuthConfig
from belka.auth.manager import BaseAuthUserManager

UserT = TypeVar("UserT")

BackendFactory = Callable[[AuthConfig], AuthenticationBackend]


def make_auth_provider(
    user_model: type[UserT],
    user_manager_cls: type[BaseAuthUserManager[UserT]],
    *,
    backend_factory: BackendFactory = make_cookie_backend,
) -> Provider:
    """Собирает dishka-провайдер для belka.auth.

    Ожидает, что ``AuthConfig`` и ``AsyncSession`` уже предоставлены
    внешними провайдерами (APP и REQUEST соответственно).

    На выходе:
    - ``AuthenticationBackend`` в APP-скоупе (по умолчанию — cookie).
    - ``SQLAlchemyUserDatabase`` в REQUEST-скоупе, привязанная
      к конкретной модели пользователя приложения.
    - ``BaseAuthUserManager`` в REQUEST-скоупе, со секретами из ``AuthConfig``.
    """

    class AuthProvider(Provider):
        @provide(scope=Scope.APP)
        def auth_backend(self, config: AuthConfig) -> AuthenticationBackend:
            return backend_factory(config)

        @provide(scope=Scope.REQUEST)
        def user_db(
            self,
            session: AsyncSession,
        ) -> SQLAlchemyUserDatabase[UserT, uuid.UUID]:
            return SQLAlchemyUserDatabase(session, user_model)

        @provide(scope=Scope.REQUEST)
        def user_manager(
            self,
            user_db: SQLAlchemyUserDatabase[UserT, uuid.UUID],
            config: AuthConfig,
        ) -> BaseAuthUserManager[UserT]:
            return user_manager_cls(
                user_db,
                reset_password_token_secret=config.reset_password_secret,
                verification_token_secret=config.verification_secret,
            )

    return AuthProvider()


__all__ = ["BackendFactory", "make_auth_provider"]
