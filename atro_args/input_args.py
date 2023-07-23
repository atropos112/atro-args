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
from atro_args.arg_type import ArgType


class InputArgs(BaseModel):
    prefix: UpperCase
    args: list[Arg] = []
    env_files: list[Path] = [Path(".env")]
    yaml_files: list[Path] = []
    arg_priority: list[ArgType] = [ArgType.cli_args, ArgType.yaml_files, ArgType.envs, ArgType.env_files]

    @field_validator("arg_priority")
    def arg_priority_must_be_unique_and_size_four(cls, v):
        if len(v) != 4:
            raise ValueError("arg_priority must be of size 4")
        if len(set(v)) != 4:
            raise ValueError("arg_priority must be unique")
        return v

    def add_arg(self, arg: Arg):
        self.args.append(arg)

    def get_cli_args(self, cli_input_args: Sequence[str] | None) -> dict[str, str]:
        parser = ArgumentParser()
        for arg in self.args:
            if arg.accept_via_cli:
                parser.add_argument(f"--{arg.name}", *arg.other_names, type=arg.arg_type, help=arg.help, required=False)

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

    def populate_if_empty(self, model: dict[str, Any], inputs: dict[str, str], input_name: str) -> None:
        for key, value in inputs.items():
            logging.debug(f"Considering key: '{key},' value: '{value}' from '{input_name}'")

            if key not in model:
                logging.debug(f"'{key}' has not been requested as an argument, skipping.")
                continue

            if value is None:
                logging.debug(f"'{key}' is not populated in '{input_name}'.")
                continue

            if model.get(key) is None:
                logging.info(f"Setting '{key}' to be of value '{value}' from '{input_name}'")
                (arg_type,) = (arg.arg_type for arg in self.args if arg.name == key)
                if type(value) == arg_type:
                    model[key] = value
                else:
                    logging.debug("Casting '{value}' to type '{arg_type}'")
                    try:
                        model[key] = arg_type(value)
                    except Exception as e:
                        logging.fatal(f"Could not cast '{value}' to type '{arg_type}'")
                        raise TypeError(f"Could not cast '{value}' to type '{arg_type}'") from e
            else:
                logging.debug(f"'{key}' has already been set.")

    def populated_model(self, model: dict[str, Any], cli_args: dict[str, str], env_args: dict[str, str], env_file_args: dict[str, str], yaml_file_args: dict[str, str]) -> dict[str, Any]:
        for arg_type in self.arg_priority:
            match arg_type:
                case ArgType.cli_args:
                    self.populate_if_empty(model, cli_args, "cli arguments")
                case ArgType.envs:
                    self.populate_if_empty(model, env_args, "environment variables")
                case ArgType.env_files:
                    self.populate_if_empty(model, env_file_args, "environment file variables")
                case ArgType.yaml_files:
                    self.populate_if_empty(model, yaml_file_args, "yaml file variables")

        return model

    def throw_if_required_not_populated(self, model: dict[str, Any]) -> None:
        missing_but_required: list[str] = []

        for arg in self.args:
            if arg.required and model.get(arg.name) is None:
                missing_but_required.append(arg.name)

        if len(missing_but_required) > 0:
            raise Exception(f"Missing required arguments: '{', '.join(missing_but_required)}'")

    def parse_args(self, cli_input_args: Sequence[str] | None = None) -> dict[str, Any]:
        model: dict[str, Any] = {arg.name: None for arg in self.args}

        cli_args = self.get_cli_args(cli_input_args)
        env_args = self.get_env_args()
        env_file_args = self.get_env_file_args()
        yaml_file_args = self.get_yaml_file_args()

        populated_model = self.populated_model(model, cli_args, env_args, env_file_args, yaml_file_args)

        self.throw_if_required_not_populated(populated_model)

        return populated_model
