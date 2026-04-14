from pathlib import Path

import pytest
from typer.testing import CliRunner

from belka.cli.__main__ import app


runner = CliRunner()


@pytest.fixture
def workdir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _assert_compiles(path: Path) -> None:
    compile(path.read_text(encoding="utf-8"), str(path), "exec")


def test_domain_generates_all_files(workdir: Path) -> None:
    result = runner.invoke(app, ["generate", "domain", "auth_rbac", "role"])
    assert result.exit_code == 0, result.output

    domain = workdir / "src" / "auth_rbac" / "role"
    for filename in ("__init__.py", "models.py", "schemas.py", "repositories.py", "uow.py"):
        target = domain / filename
        assert target.exists(), f"missing {target}"
        _assert_compiles(target)


def test_domain_content_uses_conventions(workdir: Path) -> None:
    runner.invoke(app, ["generate", "domain", "auth_rbac", "role"])
    domain = workdir / "src" / "auth_rbac" / "role"

    models = (domain / "models.py").read_text()
    assert "class Role(Base):" in models
    assert 'role_id = synonym("id")' in models

    schemas = (domain / "schemas.py").read_text()
    assert "class RoleSchema(SchemaModel):" in schemas
    assert "role_id: int" in schemas
    assert "class RoleResponse(RoleSchema, ResponseModel):" in schemas
    assert "class RoleCreateRequest(RequestModel):" in schemas
    assert "class RoleUpdateRequest(RequestModel):" in schemas

    repos = (domain / "repositories.py").read_text()
    assert "class RoleRepository(SQLAlchemyRepository[RoleSchema]):" in repos
    assert "_model = Role" in repos

    uow = (domain / "uow.py").read_text()
    assert "class RoleUnitOfWork(UnitOfWork):" in uow
    assert "roles: RoleRepository" in uow


def test_domain_refuses_overwrite_without_force(workdir: Path) -> None:
    runner.invoke(app, ["generate", "domain", "auth_rbac", "role"])
    result = runner.invoke(app, ["generate", "domain", "auth_rbac", "role"])
    assert result.exit_code != 0


def test_domain_force_overwrites(workdir: Path) -> None:
    runner.invoke(app, ["generate", "domain", "auth_rbac", "role"])
    (workdir / "src" / "auth_rbac" / "role" / "models.py").write_text("# dirty")
    result = runner.invoke(app, ["generate", "domain", "auth_rbac", "role", "--force"])
    assert result.exit_code == 0, result.output
    assert "# dirty" not in (workdir / "src" / "auth_rbac" / "role" / "models.py").read_text()


@pytest.mark.parametrize(
    "kind,filename,marker",
    [
        ("model", "models.py", "class Camera(Base):"),
        ("schema", "schemas.py", "class CameraSchema(SchemaModel):"),
        ("repository", "repositories.py", "class CameraRepository"),
        ("uow", "uow.py", "class CameraUnitOfWork"),
    ],
)
def test_single_file_subcommands(workdir: Path, kind: str, filename: str, marker: str) -> None:
    result = runner.invoke(app, ["generate", kind, "camera", "camera"])
    assert result.exit_code == 0, result.output
    target = workdir / "src" / "camera" / "camera" / filename
    assert target.exists()
    assert marker in target.read_text()


def test_pluralize_attr_name_irregular(workdir: Path) -> None:
    runner.invoke(app, ["generate", "uow", "camera", "box"])
    uow = (workdir / "src" / "camera" / "box" / "uow.py").read_text()
    assert "boxes: BoxRepository" in uow


def test_custom_path(workdir: Path) -> None:
    result = runner.invoke(app, ["generate", "domain", "auth_rbac", "role", "--path", "app"])
    assert result.exit_code == 0, result.output
    assert (workdir / "app" / "auth_rbac" / "role" / "models.py").exists()


def test_pascal_name_normalized(workdir: Path) -> None:
    result = runner.invoke(app, ["generate", "domain", "auth_rbac", "UserRole"])
    assert result.exit_code == 0, result.output
    domain = workdir / "src" / "auth_rbac" / "user_role"
    assert (domain / "models.py").exists()
    assert "class UserRole(Base):" in (domain / "models.py").read_text()
    assert "user_role_id = synonym" in (domain / "models.py").read_text()
