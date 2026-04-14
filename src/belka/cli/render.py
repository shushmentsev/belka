from jinja2 import Environment, PackageLoader, StrictUndefined

from belka.cli.naming import pluralize, to_pascal, to_snake


_env = Environment(
    loader=PackageLoader("belka.cli", "templates"),
    keep_trailing_newline=True,
    undefined=StrictUndefined,
)


def build_context(name: str, module: str) -> dict[str, str]:
    snake = to_snake(name)
    return {
        "module": module,
        "name": snake,
        "class_name": to_pascal(snake),
        "table_name": snake,
        "pk_field": f"{snake}_id",
        "attr_name": pluralize(snake),
    }


def render(template: str, context: dict[str, str]) -> str:
    return _env.get_template(template).render(**context)
