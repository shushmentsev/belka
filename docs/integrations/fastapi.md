# Использование с FastAPI

`belka` поставляется с готовым `dishka`-провайдером, который предоставляет
`async_sessionmaker` (scope `APP`) и `AsyncSession` (scope `REQUEST`).
В связке с `dishka.integrations.fastapi` это даёт сессию SQLAlchemy на каждый
HTTP-запрос без ручного управления зависимостями.

## Установка

```bash
pip install "belka[dishka]" dishka fastapi uvicorn
```

## Минимальный пример

```python
from dishka import make_async_container
from dishka.integrations.fastapi import FromDishka, inject, setup_dishka
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncSession

from belka.integrations.dishka import DatabaseConfig, DatabaseProvider


def create_app() -> FastAPI:
    app = FastAPI()

    container = make_async_container(
        DatabaseProvider(),
        context={
            DatabaseConfig: DatabaseConfig(
                dsn="postgresql+asyncpg://user:pass@localhost/db",
            ),
        },
    )
    setup_dishka(container, app)

    @app.get("/users/{user_id}")
    @inject
    async def get_user(
        user_id: int,
        session: FromDishka[AsyncSession],
    ) -> dict:
        result = await session.execute(
            text("SELECT name FROM users WHERE id = :id"),
            {"id": user_id},
        )
        row = result.first()
        return {"name": row.name if row else None}

    return app
```

## Подключение собственного репозитория

`SQLAlchemyRepository` принимает сессию в конструкторе, поэтому её удобно
оформить как отдельный провайдер:

```python
from dishka import Provider, Scope, provide

from belka.core.repository import SQLAlchemyRepository
from myapp.models import User
from myapp.schemas import UserSchema


class UserRepository(SQLAlchemyRepository[UserSchema]):
    _model = User


class RepositoryProvider(Provider):
    user_repository = provide(UserRepository, scope=Scope.REQUEST)
```

```python
container = make_async_container(
    DatabaseProvider(),
    RepositoryProvider(),
    context={DatabaseConfig: DatabaseConfig(dsn=...)},
)
```

В обработчике:

```python
@app.get("/users/{user_id}")
@inject
async def get_user(
    user_id: int,
    users: FromDishka[UserRepository],
) -> UserSchema | None:
    return await users.get_by_id(user_id)
```

## Конфигурация из окружения

`DatabaseConfig` — обычный `frozen` dataclass, поэтому удобно собирать его
из любого источника настроек (pydantic-settings, environ, dynaconf и т.п.):

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_dsn: str


settings = Settings()
container = make_async_container(
    DatabaseProvider(),
    context={DatabaseConfig: DatabaseConfig(dsn=settings.database_dsn)},
)
```

## Жизненный цикл

- `async_sessionmaker` создаётся один раз на приложение (`Scope.APP`).
- `AsyncSession` открывается на каждый запрос и закрывается автоматически
  при выходе из `async with` внутри провайдера.
- Транзакции коммитятся через `UnitOfWork` — см. `belka.core.uow`.
