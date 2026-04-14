import typer

from belka.cli.commands import generate


app = typer.Typer(help="belka — генерация скелетов доменов и утилиты.")
app.add_typer(generate.app, name="generate")


if __name__ == "__main__":
    app()
