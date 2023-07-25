import logging
from argparse import ArgumentParser
from collections.abc import Sequence
from os import environ
from pathlib import Path
from typing import Any

import yaml
from annotated_types import UpperCase
from dotenv import load_dotenv
from pydantic import BaseModel, field_validator

from atro_args.arg import Arg
from atro_args.arg_source import ArgSource
from atro_args.helpers import load_as_py_type_from_string


class InputArgs(BaseModel):
    """InputArgs is a model that represents the input arguments of an application. After it is initialized the parse_args method can be called to parse the arguments and return them as a dictionary.

    Attributes:
        prefix (UpperCase): The prefix to use for environment variables. Defaults to "ATRO_ARGS". This means that the environment variable for the argument "name" will be "ATRO_ARGS_NAME" and the environment variable for the argument "other_names" will be "ATRO_ARGS_OTHER_NAMES".
        args (list[Arg], optional): A list of arguments to parse. Defaults to [].
        env_files (list[Path], optional): A list of paths to environment files. Defaults to [Path(".env")] which is the .env file in the directory where the application is ran from.
        yaml_files (list[Path], optional): A list of paths to yaml files. Defaults to [].
        arg_priority: (list[ArgSource], optional): A list of ArgSource enums that represent the priority of the arguments. Defaults to [ArgSource.cli_args, ArgSource.yaml_files, ArgSource.envs, ArgSource.env_files]. This means that if an argument is passed via CLI it will take priority over the same argument passed via a yaml file, which will take priority over the same argument passed via ENV, which will take priority over the same argument passed via an ENV file.
    """

    prefix: UpperCase = "ATRO_ARGS"
    args: list[Arg] = []
    env_files: list[Path] = [Path(".env")]
    yaml_files: list[Path] = []
    arg_priority: list[ArgSource] = [ArgSource.cli_args, ArgSource.yaml_files, ArgSource.envs, ArgSource.env_files]

    @field_validator("arg_priority")
    def arg_priority_must_be_unique_and_size_four(cls, v):
        if len(set(v)) != len(v):
            raise ValueError("arg_priority must be unique")
        return v

    def add_arg(self, arg: Arg):
        self.args.append(arg)

    def get_cli_args(self, cli_input_args: Sequence[str] | None) -> dict[str, str]:
        parser = ArgumentParser()
        for arg in self.args:
            if arg.accept_via_cli:
                parser.add_argument(f"--{arg.name}", *arg.other_names, type=str, help=arg.help, required=False)

        return vars(parser.parse_args(cli_input_args or []))

    def get_env_args(self) -> dict[str, str]:
        envs: dict[str, str] = {}
        for arg in self.args:
            env = environ.get(f"{self.prefix}_{arg.name}".upper())
            if env is not None:
                envs[arg.name] = env
        return envs

    def get_env_file_args(self) -> dict[str, str]:
        # Remove any existing envs
        # Load envs from file
        # Get envs
        # Restore envs from before
        # Return envs

        copy_current_envs = environ.copy()

        environ.clear()
        for env_file in self.env_files:
            load_dotenv(dotenv_path=env_file)
        envs = self.get_env_args()
        environ.clear()

        environ.update(copy_current_envs)

        return envs

    @staticmethod
    def load_yaml_to_dict(yaml_file):
        with open(yaml_file) as file:
            return yaml.safe_load(file)

    @staticmethod
    def merge_dicts(dict1, dict2):
        result = dict1.copy()
        result.update(dict2)
        return result

    def get_yaml_file_args(self):
        file_paths = self.yaml_files
        output = {}
        for file_path in file_paths:
            yaml_dict = self.load_yaml_to_dict(file_path)
            output = self.merge_dicts(output, yaml_dict)
        return output

    def populate_if_empty(self, model: dict[str, Any], inputs: dict[str, str], arg_source: ArgSource) -> None:
        for key, value in inputs.items():
            logging.debug(f"Considering key: '{key},' value: '{value}' from '{arg_source.value}'")

            if key not in model:
                logging.debug(f"'{key}' has not been requested as an argument, skipping.")
                continue

            if value is None:
                logging.debug(f"'{key}' is not populated in '{arg_source.value}'.")
                continue

            if model.get(key) is None:
                (arg,) = (arg for arg in self.args if arg.name == key)

                if self.is_arg_source_accepted(arg, arg_source) is False:
                    logging.debug(f"'{key}' is not accepted via '{arg_source.value}', skipping.")
                    continue

                logging.info(f"Setting '{key}' to be of value '{value}' from '{arg_source.value}'")
                if type(value) == arg.arg_type:
                    model[key] = value
                else:
                    logging.debug("Parsing {value} as {arg.arg_type}.")
                    model[key] = load_as_py_type_from_string(value, arg.arg_type)

            else:
                logging.debug(f"'{key}' has already been set.")

    def populated_model(self, model: dict[str, Any], cli_args: dict[str, str], env_args: dict[str, str], env_file_args: dict[str, str], yaml_file_args: dict[str, str]) -> dict[str, Any]:
        for arg_type in self.arg_priority:
            match arg_type:
                case ArgSource.cli_args:
                    self.populate_if_empty(model, cli_args, ArgSource.cli_args)
                case ArgSource.envs:
                    self.populate_if_empty(model, env_args, ArgSource.envs)
                case ArgSource.env_files:
                    self.populate_if_empty(model, env_file_args, ArgSource.env_files)
                case ArgSource.yaml_files:
                    self.populate_if_empty(model, yaml_file_args, ArgSource.yaml_files)

        return model

    @staticmethod
    def is_arg_source_accepted(arg: Arg, arg_source: ArgSource) -> bool:
        match arg_source:
            case ArgSource.cli_args:
                return arg.accept_via_cli
            case ArgSource.envs:
                return arg.accept_via_env
            case ArgSource.env_files:
                return arg.accept_via_env_file
            case ArgSource.yaml_files:
                return arg.accept_via_yaml_file

    def throw_if_required_not_populated(self, model: dict[str, Any]) -> None:
        missing_but_required: list[str] = []

        for arg in self.args:
            if arg.required and model.get(arg.name) is None:
                missing_but_required.append(arg.name)

        if len(missing_but_required) > 0:
            raise Exception(f"Missing required arguments: '{', '.join(missing_but_required)}'")

    def parse_args(self, cli_input_args: Sequence[str] | None = None) -> dict[str, Any]:
        """Parses the arguments and returns them as a dictionary from (potentially) multiple sources.

        Examples:
            >>> from atro_args import InputArgs, Arg
            >>> input_arg = InputArgs()
            >>> input_arg.add_arg(Arg(name="a", arg_type=float, help="The first addend in the addition."))
            >>> input_arg.parse_args()
            {'a': 1.23}

        Args:
            cli_input_args (Sequence[str]): A list of strings representing the CLI arguments. Defaults to None which means the arguments will be read from sys.argv.

        Returns:
            A dictionary with keys being the argument names and values being the argument values. Argument values will be of the type specified in the Arg model.
        """
        
        model: dict[str, Any] = {arg.name: arg.default for arg in self.args}

        cli_args = self.get_cli_args(cli_input_args)
        env_args = self.get_env_args()
        env_file_args = self.get_env_file_args()
        yaml_file_args = self.get_yaml_file_args()

        populated_model = self.populated_model(model, cli_args, env_args, env_file_args, yaml_file_args)

        self.throw_if_required_not_populated(populated_model)
        return populated_model
