import os
import sys

from click import MissingParameter, Context

sys.path.append(os.getcwd())

from src.configurator.run import run, set_logger, set_theme
from src.helpers.pretty_str import default_theme

theme = default_theme

if __name__ == '__main__':
    set_logger(name="DDOCS", theme=theme, output="./logs")
    set_theme(theme)
    run(obj={})


# import click
# import questionary


# class QuestionaryOption(click.Option):
#
#     def __init__(self, param_decls=None, **attrs):
#         click.Option.__init__(self, param_decls, **attrs)
#         if not isinstance(self.type, click.Choice):
#             raise Exception('ChoiceOption type arg must be click.Choice')
#
#     def prompt_for_value(self, ctx):
#         val = questionary.select(self.prompt, choices=self.type.choices, show_selected=True,).ask()
#         return val
#
#     def process_value(self, ctx: Context, value):
#         value = self.type_cast_value(ctx, value)
#
#         if self.required and self.value_is_missing(value):
#             raise MissingParameter(ctx=ctx, param=self)
#
#         if self.callback is not None:
#             value = self.callback(ctx, self, value)
#         print(value)
#         return value
#
#
# @click.command()
# @click.option('--hash-type', prompt='Hash', type=click.Choice(['MD5', 'SHA1'], case_sensitive=False, ), cls=QuestionaryOption)
# def cli(**kwargs):
#     print(kwargs)
#
#
# if __name__ == "__main__":
#     cli()