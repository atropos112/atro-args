import configparser
import json
import tomllib
from collections.abc import Sequence
from os import environ
from pathlib import Path
from sys import argv
from typing import Any

import yaml
from dotenv import load_dotenv

from atro_args.entities.arg import Arg
from atro_args.entities.arg_source import ArgSource

# region loader


def load_source(source: ArgSource | Path, prefix: str, args: Sequence[Arg], cli_input_args: Sequence[str] | None = None) -> dict[str, Any]:
    """Loads the arguments from the source provided. The source can be a file or a source of arguments like CLI or ENVs.

    Args:
        source (ArgSource | Path): The source either the type like cli_args/envs or a path to a file.
        prefix (str): prefix for the envs.
        args (Sequence[Arg]): The arguments to load, need to understand how to resolve names from envs.
        cli_input_args (Sequence[str] | None, optional): Allows cli_inputs_args to simulate the CLI arguments passed to the program. Defaults to None. To simulate input like "--arg1 value1 --arg2 value2 -a value3 --arg4=value4" pass ["--arg1", "value1", "--arg2", "value2", "-a", "value3", "--arg4=value4"] or ["--arg1", "value1", "--arg2", "value2", "-a", "value3", "--arg4", "value4"] both will work.

    Raises:
        Exception: If the file type is not supported an exception is raised.

    Returns:
        dict[str, str]: dictionary of strings representing the arguments passed to the program, where key is the argument name and value is the argument value. The values are all strings and need to be parsed to the correct type.
    """

    output = {}
    print(source)
    match source:
        case ArgSource.cli:
            output = get_cli_args(cli_input_args)
        case ArgSource.envs:
            output = get_env_args(prefix, args)
        case Path:
            match source.name.split(".")[-1]:  # source.suffix would not work here as .env would map to empty string
                case "env" | "":
                    output = get_env_file_args(prefix, args, source)
                case "yaml" | "yml":
                    output = get_yaml_file_args(source)
                case "json":
                    output = get_json_file_args(source)
                case "toml":
                    output = get_toml_file_args(source)
                case "ini":
                    output = get_ini_file_args(source, prefix)
                case _:
                    raise Exception(f"Tried loading {source} of type {type(source)} but failed. File type '{source.suffix}' is not supported.")

    return output


# endregion

# region CLI


def get_cli_args(cli_input_args: Sequence[str] | None = None) -> dict[str, str]:
    """get_cli_args parses the CLI arguments passed to the program as a dictionary of strings. The types are not yet parsed so the values are all strings.

    Note it is not argparse based. Arg parse exhibited some behaviours I strongly disliked namely:
    - It didn't deal well with lists, often would map str to list of chars instead of list of strings, you could mention that you want all the "following" args to somewhat remidate this but it still is not great.
    - It replaces - with _ in the argument names, this is just a hack.
    - If given no arguments and trying to use in tests, it will flat out throw, again not great.
    As such I decided to implement a very very basic version of it myself, its not even close versatile as argparse is with its many options but for this use case it is enough.


    Args:
        cli_input_args (Sequence[str] | None, optional): Allows cli_inputs_args to simulate the CLI arguments passed to the program. Defaults to None. To simulate input like "--arg1 value1 --arg2 value2 -a value3 --arg4=value4" pass ["--arg1", "value1", "--arg2", "value2", "-a", "value3", "--arg4=value4"] or ["--arg1", "value1", "--arg2", "value2", "-a", "value3", "--arg4", "value4"] both will work.

    Raises:
        ValueError: If the first argument passed does not start with "-" or "--" an error is raised as it is not clear which argument this input is for.

    Returns:
        dict[str, str]: dictionary of strings representing the arguments passed to the program, where key is the argument name and value is the argument value.
    """
    cli_inputs = cli_input_args if cli_input_args != None else argv[1:]  # cli_input_args or argv[1:] is not the same here as empty list means no inputs were provided via cli_input_args where as if its None we fall back on argv[1:] as cli_input_args was not provided.

    cli_inputs = split_by_equals(cli_inputs)
    output: dict[str, str] = {}

    if not [cli_input for cli_input in cli_inputs if cli_input.startswith("-")]:
        return output  # No arguments were passed so nothing is returned.

    current_arg = None
    for cli_input in cli_inputs:
        if cli_input.startswith("---"):
            raise ValueError(f"Argument {cli_input} passed with too many dashes.")
        elif cli_input.startswith("--"):
            current_arg = cli_input[2:]
            output[current_arg] = ""
        elif cli_input.startswith("-"):
            current_arg = cli_input[1:]
            output[current_arg] = ""
        else:
            if not current_arg:
                raise ValueError(f"Argument {cli_input} passed without a preceding argument.")
            output[current_arg] += " " + cli_input if output[current_arg] != "" else cli_input
    return output


def split_by_equals(cli_input_args: Sequence[str]) -> Sequence[str]:
    cli_inputs: list[str] = []
    for cli_input in cli_input_args:
        if "=" in cli_input:
            cli_inputs += cli_input.split("=")
        else:
            cli_inputs.append(cli_input)
    return cli_inputs


def wrapped_by(s: str, wrapper: str) -> bool:
    return s.startswith(wrapper) and s.endswith(wrapper)


def strip_first_and_last(s: str) -> str:
    return s[1:-1]


# endregion

# region ENVs


def get_all_prefixed_env_args(prefix: str) -> dict[str, str]:
    envs = environ.copy()
    prefix = prefix.upper()
    return {key[len(prefix) + 1 :].lower(): value for key, value in envs.items() if key.startswith(prefix)}


def get_env_args(prefix: str, args: Sequence[Arg]):
    all_prefixed_envs = get_all_prefixed_env_args(prefix)

    output: dict[str, str] = {}
    for arg in args:
        # If the arg name is in the envs, add it to the output
        if arg.name.lower() in all_prefixed_envs:
            output[arg.name] = all_prefixed_envs[arg.name.lower()]
        # If arg name is not in the envs, maybe one of the other names is
        elif arg.other_names:
            other_nms = [other_name.lower() for other_name in arg.other_names if other_name.lower() in all_prefixed_envs]
            if other_nms:
                (output[arg.name],) = other_nms

    return output


# endregion

# region ENV file


def get_env_file_args(prefix: str, args: Sequence[Arg], path: Path) -> dict[str, str]:
    # Remove any existing envs
    # Load envs from file
    # Get envs
    # Restore envs from before
    # Return envs

    copy_current_envs = environ.copy()

    environ.clear()
    load_dotenv(dotenv_path=path)
    envs = get_env_args(prefix, args)
    environ.clear()

    environ.update(copy_current_envs)

    return envs


# endregion

# region YAML file


def get_yaml_file_args(path: Path) -> dict[str, Any]:
    with open(path) as file:
        return yaml.safe_load(file)


# endregion

# region JSON file


def get_json_file_args(path: Path) -> dict[str, Any]:
    with open(path) as file:
        return json.load(file)


# endregion

# region TOML file


def get_toml_file_args(path: Path) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)


# endregion

# region INI file


def get_ini_file_args(source: Path, prefix: str) -> dict[str, str]:
    config = configparser.ConfigParser()
    config.read(source)

    cfgs = dict(config)[prefix]
    output = {i: cfgs[i] for i in cfgs}

    return output


# endregion
