import logging
from argparse import ArgumentParser
from collections.abc import Mapping, Sequence
from dataclasses import is_dataclass
from os import environ
from pathlib import Path
from typing import Any, TypeVar

from annotated_types import UpperCase
from dotenv import load_dotenv
from pydantic import BaseModel, model_validator

from atro_args.arg import Arg
from atro_args.arg_source import ArgSource
from atro_args.helpers import get_duplicates, load_to_py_type, load_yaml_to_dict, merge_dicts

T = TypeVar("T")


class InputArgs(BaseModel):
    """InputArgs is a model that represents the input arguments of an application. After it is initialized the parse_args method can be called to parse the arguments and return them as a dictionary.

    Attributes:
        prefix (UpperCase): The prefix to use for environment variables. Defaults to "ATRO_ARGS". This means that the environment variable for the argument "name" will be "ATRO_ARGS_NAME" and the environment variable for the argument "other_names" will be "ATRO_ARGS_OTHER_NAMES".
        args (list[Arg], optional): A list of arguments to parse. Defaults to [].
        env_files (list[Path], optional): A list of paths to environment files. Defaults to [Path(".env")] which is the .env file in the directory where the application is ran from.
        yaml_files (list[Path], optional): A list of paths to yaml files. Defaults to [].
        arg_priority: (list[ArgSource], optional): A list of ArgSource enums that represent the priority of the arguments. This means that if an argument is passed via CLI it will take priority over the same argument passed via a yaml file and so on.
    """

    prefix: UpperCase = "ATRO_ARGS"
    args: list[Arg] = []
    env_files: list[Path] = [Path(".env")]
    yaml_files: list[Path] = []
    arg_priority: list[ArgSource] = [ArgSource.cli_args, ArgSource.yaml_files, ArgSource.envs, ArgSource.env_files]

    # region Validators
    @model_validator(mode="after")
    def validate_model(self) -> "InputArgs":
        self.validate_arg_priority()
        self.validate_args()
        return self

    def validate_arg_priority(self):
        if len(set(self.arg_priority)) != len(self.arg_priority):
            dupes = get_duplicates(self.arg_priority)
            raise ValueError("The elements of list arg_priority must be unique. The following elements are duplicated: " + ", ".join(dupes) + ".")

    def validate_args(self):
        names = [arg.name for arg in self.args]
        if len(set(names)) != len(names):
            dupes = get_duplicates(names)
            raise ValueError("Can't have two or more Args with the same name parameter. The following names are duplicated: " + ", ".join(dupes) + ".")

    # endregion

    # region Adding arguments
    def add_arg(self, arg: Arg) -> None:
        self.args.append(arg)
        self.validate_args()

    def add_args(self, args: list[Arg]) -> None:
        for arg in args:
            self.add_arg(arg)
        self.validate_args()

    def add(self, name: str, other_names: str | list[str] = [], arg_type: type = str, help: str = "", required: bool = True, default: Any = None):
        self.args.append(Arg(name=name, other_names=other_names, arg_type=arg_type, help=help, required=required, default=default))
        self.validate_args()

    def add_cls(self, class_type: type) -> None:
        if is_dataclass(class_type):
            self.__add_dataclass(class_type)
        elif issubclass(class_type, BaseModel):
            self.__add_pydantic(class_type)

    # endregion

    # region Get data back
    def get_dict(self, cli_input_args: Sequence[str] | None = None) -> dict[str, Any]:
        """Parses the arguments and returns them as a dictionary from (potentially) multiple sources.

        Examples:
            >>> from atro_args import InputArgs, Arg
            >>> input_arg = InputArgs()
            >>> input_arg.add_arg(Arg(name="a", arg_type=float, help="The first addend in the addition."))
            >>> input_arg.get_dict()
            {'a': 1.23}

        Args:
            cli_input_args (Sequence[str]): A list of strings representing the CLI arguments. Defaults to None which means the arguments will be read from sys.argv.

        Returns:
            A dictionary with keys being the argument names and values being the argument values. Argument values will be of the type specified in the Arg model.
        """

        model: dict[str, Any] = {arg.name: None for arg in self.args}

        cli_args = self.__get_cli_args(cli_input_args)
        env_args = self.__get_env_args()
        env_file_args = self.__get_env_file_args()
        yaml_file_args = self.__get_yaml_file_args()

        populated_model = self.__populated_model(model, cli_args, env_args, env_file_args, yaml_file_args)

        self.__throw_if_required_not_populated(populated_model)
        return populated_model

    def get_cls(self, class_type: type[T], cli_input_args: Sequence[str] | None = None) -> T:
        if is_dataclass(class_type):
            return self.__get_dataclass(class_type, cli_input_args=cli_input_args)
        elif issubclass(class_type, BaseModel):
            return self.__get_pydantic(class_type, cli_input_args=cli_input_args)
        else:
            raise Exception(f"Class type '{class_type}' is not supported.")

    # endregion

    # region "Private" methods
    def __add_pydantic(self, pydantic_class_type: type[BaseModel]) -> None:
        for key, val in pydantic_class_type.model_fields.items():
            self.add_arg(Arg(name=key, arg_type=val.annotation, required=val.is_required(), default=None if str(val.default) == "PydanticUndefined" else val.default))  # type: ignore
        self.validate_args()

    def __add_dataclass(self, dataclass_type: type) -> None:
        for field in dataclass_type.__dataclass_fields__.values():  # type: ignore
            self.add_arg(Arg(name=field.name, arg_type=field.type, required=False, default=field.default))

    def __get_dataclass(self, dataclass_type: type[T], cli_input_args: Sequence[str] | None = None) -> T:
        if not is_dataclass(dataclass_type):
            raise Exception(f"Developer error: '{dataclass_type}' is not a dataclass and so it shouldn't call __get_dataclass.")
        model_args_required = dataclass_type.__dataclass_fields__

        return self.__get_cls_setup(dataclass_type, model_args_required, cli_input_args=cli_input_args)

    def __get_pydantic(self, pydantic_class_type: type[T], cli_input_args: Sequence[str] | None = None) -> T:
        if not issubclass(pydantic_class_type, BaseModel):
            raise Exception(f"Developer error: '{pydantic_class_type}' is not a subclass of 'BaseModel' and so it shouldn't call __get_pydantic.")
        model_args_required = pydantic_class_type.model_fields

        return self.__get_cls_setup(pydantic_class_type, model_args_required, cli_input_args=cli_input_args)

    def __get_cls_setup(self, cls: type[T], model_args_required: dict, cli_input_args: Sequence[str] | None = None) -> T:
        args = self.get_dict(cli_input_args=cli_input_args)
        output_args = {arg: args[arg] for arg in args if arg in model_args_required.keys()}

        # Note the types might be incorret if user error at which point Pydantic will throw an exception.
        myClass = cls(**output_args)

        return myClass

    def __get_cli_args(self, cli_input_args: Sequence[str] | None = None) -> dict[str, str]:
        parser = ArgumentParser()
        for arg in self.args:
            # Making some adjustments
            other_names = ["-" + name for name in arg.other_names]
            arg_type = arg.arg_type
            if arg_type in [Sequence, Mapping, list, dict]:
                # loading a json as dict or list will fail in argparse, as it will load each element char by char, bypassing that issue by loading it as a string and then converting it to the desired type
                arg_type = str

            parser.add_argument(f"--{arg.name}", *other_names, type=arg_type, help=arg.help, required=False)
        # Using parse_known_args instead of parse_args as parse_args throws on empty input.
        output = vars(parser.parse_known_args(cli_input_args)[0]) or {}

        for name in [arg.name for arg in self.args]:
            # Edge case where argument has "-" in the name argparse would return this as _ instead.
            if "-" in name and name.replace("-", "_") in output.keys() and name not in output.keys():
                output[name] = output.pop(name.replace("-", "_"))

        return output

    def __get_env_args(self) -> dict[str, str]:
        envs: dict[str, str] = {}
        for arg in self.args:
            env = environ.get(f"{self.prefix}_{arg.name}".upper())
            if env is not None:
                envs[arg.name] = env
        return envs

    def __get_env_file_args(self) -> dict[str, str]:
        # Remove any existing envs
        # Load envs from file
        # Get envs
        # Restore envs from before
        # Return envs

        copy_current_envs = environ.copy()

        environ.clear()
        for env_file in self.env_files:
            load_dotenv(dotenv_path=env_file)
        envs = self.__get_env_args()
        environ.clear()

        environ.update(copy_current_envs)

        return envs

    def __get_yaml_file_args(self):
        file_paths = self.yaml_files
        output = {}
        for file_path in file_paths:
            yaml_dict = load_yaml_to_dict(file_path)
            output = merge_dicts(output, yaml_dict)
        return output

    def __populate_if_empty(self, model: dict[str, Any], inputs: dict[str, str], arg_source: ArgSource) -> None:
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

                logging.info(f"Setting '{key}' to be of value '{value}' from '{arg_source.value}'")
                model[key] = load_to_py_type(value, arg.arg_type)

            else:
                logging.debug(f"'{key}' has already been set.")

    def __populated_model(self, model: dict[str, Any], cli_args: dict[str, str], env_args: dict[str, str], env_file_args: dict[str, str], yaml_file_args: dict[str, str]) -> dict[str, Any]:
        for arg_type in self.arg_priority:
            match arg_type:
                case ArgSource.cli_args:
                    self.__populate_if_empty(model, cli_args, ArgSource.cli_args)
                case ArgSource.envs:
                    self.__populate_if_empty(model, env_args, ArgSource.envs)
                case ArgSource.env_files:
                    self.__populate_if_empty(model, env_file_args, ArgSource.env_files)
                case ArgSource.yaml_files:
                    self.__populate_if_empty(model, yaml_file_args, ArgSource.yaml_files)
                case _:
                    self.__populate_if_empty(model, {arg.name: arg.default for arg in self.args}, ArgSource.defaults)

        return model

    def __throw_if_required_not_populated(self, model: dict[str, Any]) -> None:
        missing_but_required: list[str] = []

        for arg in self.args:
            if arg.required and model.get(arg.name) is None:
                missing_but_required.append(arg.name)

        if len(missing_but_required) > 0:
            raise Exception(f"Missing required arguments: '{', '.join(missing_but_required)}'")

    # endregion
