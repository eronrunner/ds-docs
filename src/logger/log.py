import sys
from logging.handlers import RotatingFileHandler


import logging


class CustomFormatter(logging.Formatter):
    def __init__(self, fmt, *args, theme=None, **kwargs):
        self.theme = theme
        self.fmt = fmt
        if theme:
            self.formats = {
                logging.DEBUG: theme.debug(fmt),
                logging.INFO: theme.info(fmt),
                logging.WARNING: theme.warning(fmt),
                logging.ERROR: theme.error(fmt),
                logging.CRITICAL: theme.critical(fmt)
            }
        else:
            self.formats = {}
        super().__init__(fmt, *args, **kwargs)

    def format(self, record):
        log_fmt = self.formats.get(record.levelno) if self.theme else self.fmt
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


class Logger(logging.Logger):
    def __init__(self, name: str, output: str, theme=None,
                 fmt="[%(asctime)s] - [%(name)s] - [%(levelname)s] - %(message)s",
                 level: int = logging.DEBUG):
        super().__init__(name, level)
        self.setLevel(level)
        self.formatter = CustomFormatter(theme=theme, fmt="%(message)s")
        self.stream_handler = logging.StreamHandler(sys.stdout)
        self.addHandler(self.stream_handler)
        self.stream_handler.setFormatter(self.formatter)
        self.file_handler = RotatingFileHandler(
            f"{output}/logs-out.log", maxBytes=100000, backupCount=10
        )
        _fmt = logging.Formatter(fmt)
        self.file_handler.setFormatter(_fmt)
        self.addHandler(self.file_handler)

    def set_level(self, level: int):
        self.setLevel(level)

    def set_formatter(self, formatter: logging.Formatter):
        self.formatter = formatter
        self.file_handler.setFormatter(self.formatter)

    def set_stream_handler(self, handler: logging.StreamHandler):
        self.stream_handler = handler
        self.addHandler(self.stream_handler)

    def set_file_handler(self, file_handler: RotatingFileHandler):
        self.file_handler = file_handler
        self.addHandler(self.file_handler)

