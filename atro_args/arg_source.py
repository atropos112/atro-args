from enum import Enum


class ArgSource(Enum):
    """Enum for the non-file source of an argument. This doesn't included sources that are file based.

    Attributes:
        value (str): The value of the enum. Possible choices are "cli_args" or "envs".
    """

    cli_args = "cli_args"
    envs = "envs"
