from enum import Enum


class ArgSource(Enum):
    """Enum for the source of an argument.

    Attributes:
        value (str): The value of the enum. Possible choices are "cli_args", "envs", "env_files" and "yaml_files".
    """

    cli_args = "cli_args"
    envs = "envs"
    env_files = "env_files"
    yaml_files = "yaml_files"
