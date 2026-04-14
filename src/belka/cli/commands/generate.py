from pathlib import Path

import typer

from belka.cli.render import build_context, render


app = typer.Typer(help="Скафолдинг доменов по соглашениям belka.")


_SINGLE_FILE_TEMPLATES = {
    "model": "models.py.j2",
    "schema": "schemas.py.j2",
    "repository": "repositories.py.j2",
    "uow": "uow.py.j2",
}

_BUNDLE_FILES = {
    "__init__.py": "__init__.py.j2",
    "models.py": "models.py.j2",
    "schemas.py": "schemas.py.j2",
    "repositories.py": "repositories.py.j2",
    "uow.py": "uow.py.j2",
}


def _write(target: Path, content: str, force: bool) -> None:
    if target.exists() and not force:
        raise typer.BadParameter(
            f"{target} уже существует; используйте --force для перезаписи"
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")
    typer.echo(f"created {target}")


def _domain_dir(path: Path, module: str, name: str) -> Path:
    return path / module / name


@app.command("domain")
def domain(
    module: str = typer.Argument(..., help="Родительский пакет (например auth_rbac)."),
    name: str = typer.Argument(..., help="Имя сущности в snake_case (например role)."),
    path: Path = typer.Option(Path("src"), "--path", help="Корень исходников."),
    force: bool = typer.Option(False, "--force", help="Перезаписывать существующие файлы."),
) -> None:
    """Сгенерировать полный домен: models, schemas, repositories, uow."""
    context = build_context(name, module)
    target_dir = _domain_dir(path, module, context["name"])
    for filename, template in _BUNDLE_FILES.items():
        content = render(template, context)
        _write(target_dir / filename, content, force)


def _single_file_command(kind: str, filename: str):
    template = _SINGLE_FILE_TEMPLATES[kind]

    def command(
        module: str = typer.Argument(...),
        name: str = typer.Argument(...),
        path: Path = typer.Option(Path("src"), "--path"),
        force: bool = typer.Option(False, "--force"),
    ) -> None:
        context = build_context(name, module)
        target = _domain_dir(path, module, context["name"]) / filename
        _write(target, render(template, context), force)

    command.__doc__ = f"Сгенерировать только {filename}."
    return command


app.command("model")(_single_file_command("model", "models.py"))
app.command("schema")(_single_file_command("schema", "schemas.py"))
app.command("repository")(_single_file_command("repository", "repositories.py"))
app.command("uow")(_single_file_command("uow", "uow.py"))
