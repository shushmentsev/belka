from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    CookieTransport,
    JWTStrategy,
)

from belka.auth.config import AuthConfig


def make_jwt_strategy_factory(config: AuthConfig):
    def get_strategy() -> JWTStrategy:
        return JWTStrategy(
            secret=config.jwt_secret,
            lifetime_seconds=config.jwt_lifetime_seconds,
        )

    return get_strategy


def make_cookie_backend(
    config: AuthConfig,
    *,
    name: str = "cookie",
) -> AuthenticationBackend:
    transport = CookieTransport(
        cookie_name=config.cookie_name,
        cookie_max_age=config.cookie_max_age,
        cookie_path=config.cookie_path,
        cookie_domain=config.cookie_domain,
        cookie_secure=config.cookie_secure,
        cookie_httponly=config.cookie_httponly,
        cookie_samesite=config.cookie_samesite,
    )
    return AuthenticationBackend(
        name=name,
        transport=transport,
        get_strategy=make_jwt_strategy_factory(config),
    )


def make_bearer_backend(
    config: AuthConfig,
    *,
    name: str = "jwt",
) -> AuthenticationBackend:
    transport = BearerTransport(tokenUrl=config.bearer_token_url)
    return AuthenticationBackend(
        name=name,
        transport=transport,
        get_strategy=make_jwt_strategy_factory(config),
    )


__all__ = [
    "make_bearer_backend",
    "make_cookie_backend",
    "make_jwt_strategy_factory",
]
