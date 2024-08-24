import json
import re
import sys
from functools import wraps
from typing import Sequence, Tuple, List, Optional, Mapping, Any

import click
import questionary
from click import HelpFormatter, Abort
from click_help_colors import HelpColorsGroup, HelpColorsCommand
from pydantic import ValidationError
from questionary import Style, Choice

from src.configurator.configurator import (
    DatasourceInfoConfigurator,
    TableInfoConfigurator,
    FieldInfoConfigurator,
)
from src.logger.log import Logger
from src.model.meta import TableInfo

logger: 'Logger'
theme: 'Theme'


def set_logger(name: str, output: str, theme=None):
    global logger
    logger = Logger(name, output, theme)


def set_theme(_theme: 'Theme'):

    global theme
    theme = _theme


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
    ('disabled', 'fg:#858585 italic'),   # disabled choices for select and checkbox prompts
    ('placeholder', 'fg:#858585 italic')   # disabled choices for select and checkbox prompts
])


def context_path(relative=""):

    def decorator(func):
        func.context_path = relative
        @wraps(func)
        def wrapper(*args, **kwargs):
            ctx = args[0]
            ctx.ensure_object(dict)
            if "path" not in ctx.obj:
                ctx.obj["path"] = ["Datasource docs"]
            rs = func(*args, **kwargs)
            if ctx.invoked_subcommand:
                ctx.obj["path"].append(globals()[ctx.invoked_subcommand.replace("-", "_")].callback.context_path or ctx.invoked_subcommand)
            click.echo(theme.h1("->".join(ctx.obj["path"])))
            return rs
        return wrapper
    return decorator


def handle_error(func):

    @wraps(func)
    def decorator(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Abort:
            sys.exit(1)
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
@context_path(relative="Datasource docs")
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
@context_path(relative="Configure data source")
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
@context_path(relative="Configure table")
def configure_table(ctx, table_name, export=True) -> "TableInfo":
    """
    Configure table
    """
    # try:
    ctx.ensure_object(dict)
    table_info_configurator = TableInfoConfigurator()
    table_info_configurator.set_table_name(table_name).set_table_fields(None)
    while True:
        try:
            table_info_configurator.configure()
            break
        except (ValidationError, ValueError) as e:
            for err in e.errors():
                field_name = err["loc"][0]
                format_name = field_name.replace("_", " ").capitalize()
                _process_field_errors(table_info_configurator, err, field_name, format_name)
    # Configure fields
    configured_fields = _configure_fields(ctx, table_info_configurator)
    if configured_fields:
        logger.info(f"Table completely configured with fields: {', '.join(configured_fields)}")
    table_info = table_info_configurator.configure()
    if export:
        logger.info("Export table info . . .")
        _export(
            f"{ctx.obj['output']}/{ctx.obj['namespace']}-tableinfo-{table_name}-config.json",
            table_info.model_dump_json(by_alias=True, indent=2),
            "w+",
        )
    return table_info
    # except Exception as e:
    #     logger.error(f"Error: {e}")


def _configure_fields(ctx, table_configurator) -> list[str]:
    logger.info("Configure fields")
    configured_fields = []
    field_configurator = FieldInfoConfigurator()
    unconfigured_fields = field_configurator.get_unconfigured_fields()
    for field_name in unconfigured_fields:
        format_name = field_name.replace("_", " ").capitalize()
        _process_field(field_configurator, field_name, format_name)
    while True:
        if configured_fields:
            logger.info(f"Configured fields: {', '.join(configured_fields)}")
        try:
            field_info = field_configurator.configure()
            table_configurator.add_table_field(field_info)
            configured_fields.append(field_info.field_name)
            add_more = questionary.confirm(
                "Do you want to add more another field?"
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
        # except Exception as e:
        #     logger.error(f"Error: {e}")
    return configured_fields


def _process_field_errors(configurator: 'Configurator', err: dict, field_name: str, display_name: str = "") -> Any:
    choices = configurator.get_choices(field_name)
    logger.info(f"{display_name}, {err['msg'] if not choices else str(list(choices.keys()))}")
    return _process_field(configurator, field_name, display_name)


__NULL = "__NULL"


def _build_choices(choices: dict, default: str = None):
    _choices = []
    first_choice = None
    for k, v in choices.items():
        choice = Choice(title=k, value=v)
        if default == v:
            first_choice = choice
        _choices.append(choice)
    return _choices, first_choice


def _process_field(configurator: 'Configurator', field_name: str, display_name: str = "") -> Any:
    print("FIELD_NAME", field_name)
    field_types = configurator.get_types(field_name)
    is_hidden = field_name in _HIDDEN_FIELDS
    is_boolean = bool in field_types
    is_optional = type(None) in field_types
    choices = configurator.get_choices(field_name) if not is_boolean else {"True": True, "False": False}
    default_value = configurator.get_default(field_name)
    instruction = configurator.get_hint(field_name)
    if choices:
        if is_optional:
            choices["NOT SET"] = __NULL
        choices, first_choice = _build_choices(choices, default=default_value)
        question = questionary.select(
            f"Enter {display_name}: ",
            choices=choices,
            style=custom_style_fancy,
            instruction=instruction,
            default=first_choice
        )
    else:
        if is_hidden:
            question = questionary.password(
                f"Enter {display_name}: ",
                instruction=instruction,
                default=default_value if default_value else __NULL,
                placeholder=f"By default, set: {default_value}" if default_value else "[Your typed value will be hidden]"
            )
        else:
            question = questionary.text(
                f"Enter {display_name}: ",
                instruction=instruction,
                placeholder=str(default_value) if default_value else __NULL,

            )
    if isinstance(configurator, FieldInfoConfigurator):
        field_value = _process_field_info(configurator, field_name, question)
    else:
        field_value = question.ask()
    if field_value is None:
        raise KeyboardInterrupt
    print("SET_VALUE", field_name, field_value)
    configurator.__getattribute__(f"set_{field_name}")(
        field_value.strip() if isinstance(field_value, str) else field_value
    )
    return field_value


def _process_field_info(configurator: 'Configurator', field_name: str, question: questionary.Question) -> Any:
    field_type_value = configurator.__getattribute__("field_type")
    if _should_be_asked(field_name, field_type_value):
        field_value = question.ask()
        if field_value == __NULL:
            field_value = None
    else:
        field_value = None
    print("FIELD VALUE", type(field_value), field_value)
    return field_value


_str_asked_fields = {"field_pattern", "field_min", "field_max"}
_int_asked_fields = ("field_gt", "field_lt", "field_ge", "field_le", "field_decimal_places")
_default_asked_fields = ("field_name", "field_type", "field_alias", "field_factory", "field_required", "field_unique", "field_default_value")


def _should_be_asked(field_name: str, field_type: str):
    print("FIELD_TYPE", field_name, field_type)
    if field_name in _default_asked_fields:
        return True
    elif field_type == "text" and field_name in _str_asked_fields:
        return True
    elif field_type in ("integer", "float", "datetime") and field_name in _int_asked_fields:
        return True

    return False


@run.command("configure-tables", cls=CommandColor, help="Configure tables")
@click.pass_context
@context_path(relative="Configure tables")
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
