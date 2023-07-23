from enum import Enum


class ArgType(Enum):
    cli_args = "cli_args"
    envs = "envs"
    env_files = "env_files"
    yaml_files = "yaml_files"
