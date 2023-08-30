from enum import Enum


class ArgSource(Enum):
    """Enum for the source of an argument.

    Attributes:
        value (str): The value of the enum. Possible choices are "cli_args" or "envs".
    """

    cli_args = "cli_args"
    envs = "envs"
