from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True, slots=True)
class AuthConfig:
    jwt_secret: str
    reset_password_secret: str
    verification_secret: str
    jwt_lifetime_seconds: int = 3600
    cookie_name: str = "belka_auth"
    cookie_max_age: int | None = 3600
    cookie_secure: bool = True
    cookie_httponly: bool = True
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"
    cookie_path: str = "/"
    cookie_domain: str | None = None
    bearer_token_url: str = "auth/jwt/login"
