import argparse
import sys

from pylog import get_logger


class PyParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        if "logger" in kwargs:
            self.logger = kwargs.pop("logger")
        else:
            self.logger = get_logger()
        super().__init__(*args, **kwargs)

    def error(self, message):
        self.logger.error(message)
        self.print_help()
        sys.exit(2)
