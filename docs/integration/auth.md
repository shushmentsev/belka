# Аутентификация (FastAPI-Users)

`belka.auth` — тонкий слой поверх [FastAPI-Users](https://fastapi-users.github.io/fastapi-users/),
который даёт переиспользуемый mixin модели пользователя, базовый `UserManager`,
фабрики бэкендов аутентификации и `dishka`-провайдер. Слой не знает про роли и
разрешения — связка с `belka.rbac` выполняется на уровне приложения.

## Установка

```bash
pip install "belka[auth,dishka]" fastapi uvicorn
```

## Модель пользователя

`AuthUserMixin` — это `SQLAlchemyBaseUserTableUUID` из FastAPI-Users: набор
колонок (`id`, `email`, `hashed_password`, `is_active`, `is_superuser`,
`is_verified`) без привязки к конкретному `DeclarativeBase`. Приложение
собирает свою модель:

```python
from belka.auth import AuthUserMixin
from belka.core.models import Base


class User(AuthUserMixin, Base):
    __tablename__ = "app_user"
```

## Базовый менеджер

`BaseAuthUserManager` принимает секреты для сброса пароля и верификации через
конструктор — их не нужно хранить атрибутами класса:

```python
from belka.auth import BaseAuthUserManager


class UserManager(BaseAuthUserManager[User]):
    async def on_after_register(self, user, request=None):
        ...
```

## Конфигурация

```python
from belka.auth import AuthConfig

config = AuthConfig(
    jwt_secret="...",
    reset_password_secret="...",
    verification_secret="...",
    jwt_lifetime_seconds=3600,
    cookie_name="belka_auth",
    cookie_secure=True,
    cookie_samesite="lax",
)
```

По умолчанию дефолтный бэкенд — **cookie + JWT-strategy**: токен едет в
`HttpOnly`-cookie, что удобнее для браузерных SPA. Для API-клиентов есть
`make_bearer_backend(config)`. На проде cookie-режим требует HTTPS
(`cookie_secure=True`) и CSRF-защиты для не-GET запросов — это забота
приложения.

## Dishka-провайдер

```python
from dishka import make_async_container
from fastapi_users import FastAPIUsers
from fastapi_users.authentication import AuthenticationBackend

from belka.auth import AuthConfig, BaseAuthUserManager
from belka.auth.integration.dishka import make_auth_provider
from belka.infrastructure.database.integration.dishka import DatabaseConfig, DatabaseProvider

container = make_async_container(
    DatabaseProvider(),
    make_auth_provider(User, UserManager),
    context={
        DatabaseConfig: DatabaseConfig(dsn=...),
        AuthConfig: AuthConfig(
            jwt_secret=...,
            reset_password_secret=...,
            verification_secret=...,
        ),
    },
)
```

Провайдер предоставляет:

| Scope   | Тип                         |
|---------|-----------------------------|
| APP     | `AuthenticationBackend`     |
| REQUEST | `SQLAlchemyUserDatabase`    |
| REQUEST | `BaseAuthUserManager`       |

Для bearer-режима передайте фабрику явно:

```python
from belka.auth import make_bearer_backend

make_auth_provider(User, UserManager, backend_factory=make_bearer_backend)
```

## Подключение роутеров FastAPI-Users

`FastAPIUsers` требует callable `get_user_manager` в стиле FastAPI `Depends`.
Проще всего завести тонкий адаптер, который достаёт менеджер из контейнера:

```python
from dishka.integrations.fastapi import FromDishka, inject


@inject
async def get_user_manager(manager: FromDishka[BaseAuthUserManager[User]]):
    yield manager
```

Далее — стандартное подключение роутеров FastAPI-Users
(`fastapi_users.get_auth_router`, `get_register_router` и т. д.) с нашим
`AuthenticationBackend` из контейнера.
