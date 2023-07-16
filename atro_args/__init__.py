import argparse
import logging
import sys


class PyParser(argparse.ArgumentParser):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def error(self, message):
        logging.error(message)
        self.print_help()
        sys.exit(2)
