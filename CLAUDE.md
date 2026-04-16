# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

`belka` — переиспользуемая библиотека общего кода (репозиторий, UoW, спецификации, схемы, пагинация, auth, RBAC) поверх SQLAlchemy 2.0 + Pydantic v2. Фреймворк-агностичная; интеграции (FastAPI/Dishka/FastAPI-Users) подключаются через extras. В перспективе публикуется в PyPI. Язык коммитов, docstrings и документации — русский.

## Commands

Проект использует **uv** (не `pip`/`venv` напрямую).

```bash
uv sync --all-extras                  # установить все зависимости (включая dev и extras)
uv run pytest                          # прогнать тесты
uv run pytest tests/test_repository.py::test_get_by_id_returns_schema_when_found  # один тест
uv run ruff check src tests            # линтер
uv run mypy src                        # тайпчек
uv run belka generate domain <module> <name>   # CLI-скафолдинг домена
```

`pytest-asyncio` настроен в `asyncio_mode = "auto"` — async-тесты не требуют декоратора `@pytest.mark.asyncio`. Тесты работают на in-memory SQLite через `aiosqlite` (см. `tests/conftest.py`).

## Architecture

### Layers & dependency direction

```
core  ←  infrastructure
core  ←  auth          (extras = "auth",    fastapi-users)
core  ←  auth_rbac     (role/permission; привязка к auth на стороне приложения)
core  ←  cli           (extras = "cli",     typer + jinja2)
```

- `belka.core` — фреймворк-агностичный слой. Только `sqlalchemy>=2.0` и `pydantic>=2`. Никаких FastAPI/Dishka здесь быть не должно.
- Интеграции (`.integration.dishka`) лежат **внутри** своих пакетов (`belka.auth.integration.dishka`, `belka.infrastructure.database.integration.dishka`) и импортируют сторонние фреймворки только там.
- `belka.auth` и `belka.auth_rbac` взаимно не знают друг о друге; связь (например, `User(AuthUserMixin, Base)` с `roles`-relationship) делается на уровне конечного приложения.

### core/repository.py

`SQLAlchemyRepository[SchemaT]` — generic базовый класс, подкласс задаёт `_model: type[Base]`. `IRepository` — `Protocol` с каноническим интерфейсом (`get_by_id`, `get_by_filters`, `create[_many][_if_not_exists]`, `update_by_id`/`update_by_filters`, `delete_by_id[s]`/`delete_by_filters`, `amount`, `upsert`).

В реализации присутствуют устаревшие алиасы (`get`, `add`, `list`) — новые вызовы должны использовать канонические имена (`get_by_id`, `create`, `get_by_filters`); старые оставлены для совместимости и помечены `TODO` на удаление.

`get_by_id`/`list` возвращают либо `dict`, либо `SchemaModel`, в зависимости от того, какой метод реализован на модели: `to_dict()` или `to_schema()`. Базовый `Base` в `core/models.py` бросает `NotImplementedError` на оба — подклассы должны переопределить хотя бы один.

### core/specification.py

`Specification` инкапсулирует фильтры и join'ы для SQLAlchemy-запроса. Поддерживает `|` (or) и `&` (and) через `__or__`/`__and__`. Подкласс задаёт в `__init__` `_filter`, `_models_for_join`, `_models_for_outerjoin`, `_models_for_join_onclause`. Репозиторий вызывает `specification.set_statement(stmt)` → `is_satisfied()`. Хелперы `and_for_specifications`/`or_for_specifications` корректно обрабатывают `None`.

### core/uow.py

`UnitOfWork` — async context manager, принимает `AsyncSession` в конструкторе. В `_init_repos` он через `inspect.getmro(type(self))` и `__annotations__` автоматически создаёт атрибуты-репозитории из аннотаций подкласса:

```python
class MyUnitOfWork(UnitOfWork):
    users: UserRepository     # ← создаст self.users = UserRepository(session)
    roles: RoleRepository
```

Аннотации с `_` в начале игнорируются. Подклассы нельзя называть атрибуты приватными, если они должны стать репозиториями.

### core/models.py — `Base`

`Base` наследует `AsyncAttrs` + `DeclarativeBase`. `__tablename__` автогенерируется из имени класса: CamelCase → snake_case, причём `_relation_` → `_xref_` (пример: `RoleRelationUser` → `role_xref_user`).

### PK naming convention

Первичный ключ всегда именуется `<tablename>_id` (не `id`). На классе модели это задаётся как `synonym("id")`, когда миксины (например, `AuthUserMixin` = `SQLAlchemyBaseUserTableUUID`) уже определяют столбец `id`:

```python
class User(AuthUserMixin, Base):
    user_id = synonym("id")
```

Для собственных моделей — `id: Mapped[int] = mapped_column(...)` + `<name>_id = synonym("id")`. Шаблоны CLI-скафолдинга делают именно так.

### core/schemas.py

- `SchemaModel` — внутренние схемы (snake_case, `from_attributes=True`).
- `ApiModel` — базовый класс для внешнего API (`alias_generator=to_camel`).
- `RequestModel(ApiModel)` — `model_dump` по умолчанию с `exclude_unset=True`.
- `ResponseModel(ApiModel)` — для ответов API.

### cli

`belka generate domain <module> <name>` создаёт в `src/<module>/<name>/` пять файлов (`__init__.py`, `models.py`, `schemas.py`, `repositories.py`, `uow.py`) по Jinja2-шаблонам из `src/belka/cli/templates/`. Есть подкоманды `model`/`schema`/`repository`/`uow` для генерации одного файла. `name` приводится к snake_case, `class_name` — к PascalCase, `attr_name` — к простому плюральному (ie/s/es) через `belka.cli.naming`. Шаблоны доставляются в wheel через `[tool.hatch.build.targets.wheel.force-include]`.

### infrastructure/database

`create_session_maker(url)` возвращает `async_sessionmaker[AsyncSession]` с pool_size=50, max_overflow=20, pool_recycle=2h, pool_pre_ping=True, `autoflush=False`, `expire_on_commit=False`. Dishka-провайдер даёт `async_sessionmaker` (Scope.APP) и `AsyncSession` (Scope.REQUEST).

### auth

Тонкий слой поверх `fastapi-users`. `AuthUserMixin = SQLAlchemyBaseUserTableUUID` (UUID-first). `BaseAuthUserManager` принимает `reset_password_token_secret` и `verification_token_secret` через `__init__` — их **нельзя** держать атрибутами класса. Дефолтный backend — cookie+JWT (`make_cookie_backend`); для API-клиентов — `make_bearer_backend`.

## Conventions

- Не использовать `pip`/`python -m venv` — только `uv`.
- Русский язык в коммитах, docstrings и документации (см. `docs/integration/`).
- Не импортировать `FastAPI`/`Dishka`/`fastapi-users` из `belka.core`.
- Для новых доменов в `belka.auth_rbac/*` предпочитать CLI-скафолдинг (`belka generate domain auth_rbac <name>`), чтобы конвенции по `<name>_id`-synonym и структуре файлов соблюдались автоматически.
- Устаревшие методы репозитория (`get`, `add`, `list`) не использовать в новом коде.
