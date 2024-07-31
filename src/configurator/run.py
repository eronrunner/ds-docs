import json
import re
from functools import wraps, partial
from typing import Sequence, Tuple, List, Optional, Mapping, Any

import click
import questionary
from click import HelpFormatter
from prompt_toolkit.styles import Style

from src.logger.log import Logger
from src.model.meta import TableInfo, DATA_SOURCE_TYPES

from pydantic import ValidationError
from src.configurator.configurator import (
    DatasourceInfoConfigurator,
    TableInfoConfigurator,
    FieldInfoConfigurator,
)
from click_help_colors import HelpColorsGroup, HelpColorsCommand


logger: 'Logger'
theme: 'Theme'


def set_logger(name: str, output: str, theme=None):
    global logger
    logger = Logger(name, output, theme)


def set_theme(_theme: 'Theme'):

    global theme
    theme = _theme


from questionary import Style

custom_style_fancy = Style([
    ('qmark', 'fg:#673ab7 bold'),       # token in front of the question
    ('question', 'bold'),               # question text
    ('answer', 'fg:#f44336 bold'),      # submitted answer text behind the question
    ('pointer', 'fg:#673ab7 bold'),     # pointer used in select and checkbox prompts
    ('highlighted', 'fg:#673ab7 bold'), # pointed-at choice in select and checkbox prompts
    ('selected', 'fg:#cc5454'),         # style for a selected item of a checkbox
    ('separator', 'fg:#cc5454'),        # separator in lists
    ('instruction', ''),                # user instructions for select, rawselect, checkbox
    ('text', ''),                       # plain text
    ('disabled', 'fg:#858585 italic')   # disabled choices for select and checkbox prompts
])


def context_path(func):

    @wraps(func)
    def decorator(*args, **kwargs):
        ctx = args[0]
        ctx.ensure_object(dict)
        if "path" not in ctx.obj:
            ctx.obj["path"] = ["Datasource docs"]
        rs = func(*args, **kwargs)
        if ctx.invoked_subcommand:
            ctx.obj["path"].append(ctx.invoked_subcommand)
        click.echo(theme.h1("->".join(ctx.obj["path"])))
        return rs

    return decorator


def handle_error(func):

    @wraps(func)
    def decorator(*args, **kwargs):
        # try:
            return func(*args, **kwargs)
        # except Exception as e:
        #     global theme
        #     logger.critical(f"Error: {e}")

    return decorator


class ColorFormatter(HelpFormatter):
    options_regex = re.compile(r"-{1,2}[\w\-]+")

    def __init__(
        self,
        theme=None,
        headers_color: Optional[str] = None,
        options_color: Optional[str] = None,
        options_custom_colors: Optional[Mapping[str, str]] = None,
        indent_increment: int = 2,
        width: Optional[int] = None,
        max_width: Optional[int] = None,
    ):
        self.headers_color = headers_color
        self.options_color = options_color
        self.options_custom_colors = options_custom_colors
        self.theme = theme
        super().__init__(indent_increment, width, max_width)

    def _get_opt_names(self, option_name: str) -> List[str]:
        opts = self.options_regex.findall(option_name)
        if not opts:
            return [option_name]
        else:
            # Include this for backwards compatibility
            opts.append(option_name.split()[0])
            return opts

    def _pick_color(self, option_name: str) -> Optional[str]:
        opts = self._get_opt_names(option_name)
        for opt in opts:
            if self.options_custom_colors and (
                opt in self.options_custom_colors.keys()
            ):
                return self.options_custom_colors[opt]
        return self.options_color

    def write_usage(self, prog: str, args: str = '', prefix: Optional[str] = None) -> None:
        if prefix is None:
            prefix = 'Usage:\t'

        colorized_prefix = self.theme.h1(prefix)
        super().write_usage(prog, self.theme.h1(args), prefix=colorized_prefix)

    def write_heading(self, heading: str) -> None:
        colorized_heading = self.theme.h1(heading)
        super().write_heading(colorized_heading)

    def write_dl(
        self, rows: Sequence[Tuple[str, str]], col_max: int = 30, col_spacing: int = 2
    ) -> None:
        colorized_rows = [(self.theme.h1(row[0]), self.theme.normal(row[1])) for row in rows]
        super().write_dl(colorized_rows, col_max, col_spacing)


class GroupColor(HelpColorsGroup):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def get_help(self, ctx: click.Context) -> str:
        formatter = ColorFormatter(
            theme=theme, width=ctx.terminal_width, max_width=ctx.max_content_width
        )
        self.format_help(ctx, formatter)
        return formatter.getvalue().rstrip("\n")

    @handle_error
    def __call__(self, *args, **kwargs):
        kwargs["standalone_mode"] = False
        super().__call__(*args, **kwargs)


class CommandColor(HelpColorsCommand):

    def __int__(self):
        super().__init__()

    def get_help(self, ctx: click.Context) -> str:
        formatter = ColorFormatter(
            theme=theme, width=ctx.terminal_width, max_width=ctx.max_content_width
        )
        self.format_help(ctx, formatter)
        return formatter.getvalue().rstrip("\n")

    @handle_error
    def __call__(self, *args, **kwargs):
        kwargs["standalone_mode"] = False
        super().__call__(args, kwargs)


@click.group("Data source configurator", cls=GroupColor)
@click.option(
    "-n",
    "--namespace",
    help="File namespace to create your files",
    required=True,
    default="default",
)
@click.option(
    "-o",
    "--output",
    help="Output directory to save your files",
    required=True,
    default="./docs-out",
)
@click.help_option("--help", help="Show command guide")
@click.pass_context
@handle_error
@context_path
def run(ctx, namespace, output):
    ctx.ensure_object(dict)
    ctx.obj["namespace"] = namespace
    ctx.obj["output"] = output


DATA_SOURCE_INFO_ARGS_MAPPING = {
    "ds_name": "data_source_name",
    "ds_type": "data_source_type",
    "ds_host": "data_source_host",
    "ds_port": "data_source_port",
    "ds_user": "data_source_user",
    "ds_password": "data_source_password",
}


_HIDDEN_FIELDS = {"ds_password"}


@run.command("configure-ds", cls=CommandColor, help="Configure data source")
@click.option("--data-source-name", help="Data source name", required=True, default=None)
@click.option("--data-source-type", help="Data source type", default="")
@click.option("--data-source-host", help="Data source host", default="")
@click.option("--data-source-port", help="Data source port", default="")
@click.option("--data-source-user", help="Data source user", default="")
@click.option("--data-source-password", help="Data source password", default="")
@click.pass_context
@context_path
def configure_ds(
    ctx,
    data_source_name,
    data_source_type,
    data_source_host,
    data_source_port,
    data_source_user,
    data_source_password
):
    """
    Configure data source
    """
    ctx.ensure_object(dict)
    data_source_info_configurator = DatasourceInfoConfigurator()
    (
        data_source_info_configurator.set_ds_name(data_source_name)
        .set_ds_type(data_source_type)
        .set_ds_host(data_source_host)
        .set_ds_port(data_source_port)
        .set_ds_user(data_source_user)
        .set_ds_password(data_source_password)
    )
    while True:
        try:
            data_source_info = data_source_info_configurator.configure()
            logger.info("Export data source info . . .")
            _export(
                f"{ctx.obj['output']}/{ctx.obj['namespace']}-datasourceinfo-config.json",
                data_source_info.model_dump_json(by_alias=True, indent=2),
            )
            return
        except (ValidationError, ValueError) as e:
            print(e.errors())
            for err in e.errors():
                field_name = err["loc"][0]
                format_name = DATA_SOURCE_INFO_ARGS_MAPPING[field_name].replace(
                    "_", " "
                ).capitalize()
                _process_field_errors(data_source_info_configurator, err, field_name, format_name)


@run.command("configure-table", cls=CommandColor, help="Configure table")
@click.option("--table-name", help="Table name", default=None)
@click.pass_context
@context_path
def configure_table(ctx, table_name, export=True) -> "TableInfo":
    """
    Configure table
    """
    try:
        ctx.ensure_object(dict)
        table_info_configurator = TableInfoConfigurator()
        table_info_configurator.set_table_name(table_name)
        # Configure fields
        configured_fields = _configure_fields(ctx, table_info_configurator)
        if configured_fields:
            logger.info(f"Configured fields: {', '.join(configured_fields)}")
        table_info = table_info_configurator.configure()
        if export:
            logger.info("Export table info . . .")
            _export(
                f"{ctx.obj['output']}/{ctx.obj['namespace']}-tableinfo-{table_name}-config.json",
                table_info.model_dump_json(by_alias=True, indent=2),
                "w+",
            )
        return table_info
    except Exception as e:
        logger.error(f"Error: {e}")


def _configure_fields(ctx, table_configurator) -> list[str]:
    logger.info("Configure fields")
    configured_fields = []
    field_configurator = FieldInfoConfigurator()
    while True:
        if configured_fields:
            logger.info(f"Configured fields: {', '.join(configured_fields)}")
        try:
            field_info = field_configurator.configure()
            table_configurator.add_table_field(field_info)
            configured_fields.append(field_info.field_name)
            add_more = questionary.confirm(
                theme.normal("Do you want to add more another field? (y/n)")
                , default=True
            ).ask()
            if not add_more:
                break
            field_configurator = FieldInfoConfigurator()
        except (ValidationError, ValueError) as e:
            for err in e.errors():
                field_name = err["loc"][0]
                format_name = field_name.replace("_", " ").capitalize()
                _process_field_errors(field_configurator, err, field_name, format_name)
        except Exception as e:
            logger.error(f"Error: {e}")
    return configured_fields


def _process_field_errors(configurator: 'Configurator', err: dict, field_name: str, display_name: str = "") -> Any:
    choices = configurator.get_choices(field_name)
    logger.info(theme.h2(f"{display_name}, {err['msg'] if not choices else str(list(choices.keys()))}"))
    is_hidden = field_name in _HIDDEN_FIELDS

    if len(choices):
        question = questionary.select(f"Enter {display_name}: ", choices, style=custom_style_fancy)
    else:
        if is_hidden:
            question = questionary.password(f"Enter {display_name}: ")
        else:
            question = questionary.text(f"Enter {display_name}: ")
    if field_type_value:= configurator.__getattribute__("field_type"):
        if field_type_value == "str":

    configurator.__getattribute__(f"set_{field_name}")(
        field_value.strip()
    )
    return field_value


_str_asked_fields = {"field_type", "field_pattern", "field_min", "field_max"}
_int_asked_fields = ("field_gt", "field_lt", "field_ge", "field_le", "field_decimal_places")
_default_asked_fields = ("field_alias", "field_factory", "field_required", "field_unique", "field_default_value")


def _type_field_questions(configurator, field_name: str, field_type: str):
    if field_name in _default_asked_fields:
        return True
    elif field_type == "text" and field_name in _str_asked_fields:
        return True
    elif field_type in ("integer", "float", "datetime") and field_name in _int_asked_fields:
        if field_name == "field_gt" and configurator.__getattribute__("field_ge") is not None:
            return False
        elif field_name == "field_lt" and configurator.__getattribute__("field_le") is not None:
            return False
        elif
        return True

    return False


@run.command("configure-tables", cls=CommandColor, help="Configure tables")
@click.pass_context
@context_path
def configure_tables(ctx):
    """
    Configure table
    """
    try:
        logger.info("Configure tables")
        ctx.ensure_object(dict)
        tables = []
        configured_tables = []
        while True:
            if configured_tables:
                logger.info(f"Configured tables: {', '.join(configured_tables)}")
            table_name = click.prompt(theme.normal("Enter table name")).strip()
            table_info = ctx.invoke(configure_table.callback, table_name=table_name, export=False)
            tables.append(table_info.model_dump(by_alias=True))
            configured_tables.append(table_info.table_name)
            add_more = click.prompt(
                theme.normal("Do you want to add more another field? (y/n)")
                , default="y"
            ).strip()
            if add_more.lower() != "y":
                break
        logger.info("Export tables info . . .")
        _export(
            f"{ctx.obj['output']}/{ctx.obj['namespace']}-tableinfo-config.json",
            json.dumps(tables, indent=2),
        )
    except Exception as e:
        logger.error(f"Error: {e}")
        raise e


def _export(path, data, mode="w+"):
    with open(path, mode) as f:
        f.write(data)


if __name__ == "__main__":
    run(obj={})
