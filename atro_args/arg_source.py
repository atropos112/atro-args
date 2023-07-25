from enum import Enum


class ArgSource(Enum):
    """Enum for the source of an argument.

    Attributes:
        cli_args : CLI arguments
        envs: Environment arguments
        env_files: Environment arguments from files
        yaml_files: Yaml arguments from files
    """

    cli_args = "cli_args"
    envs = "envs"
    env_files = "env_files"
    yaml_files = "yaml_files"
