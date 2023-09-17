from collections.abc import Sequence
from dataclasses import is_dataclass
from pathlib import Path
from typing import Any, TypeVar

from annotated_types import UpperCase
from atro_utils import merge_dicts
from pydantic import BaseModel, PrivateAttr, model_validator

from atro_args.arg_casting import cast_dict_based_on_args
from atro_args.class_populating import add_dataclass, add_pydantic, get_dataclass, get_pydantic
from atro_args.entities.arg import Arg
from atro_args.entities.arg_source import ArgSource
from atro_args.helpers import get_duplicates, restrict_keys, throw_if_required_not_populated
from atro_args.source_loading import load_source

T = TypeVar("T")


class InputArgs(BaseModel):
    """InputArgs is a model that represents the input arguments of an application. After it is initialized the parse_args method can be called to parse the arguments and return them as a dictionary.

    Attributes:
        prefix (UpperCase): The prefix to use for environment variables. Defaults to "ATRO_ARGS". This means that the environment variable for the argument "name" will be "ATRO_ARGS_NAME" and the environment variable for the argument "other_names" will be "ATRO_ARGS_OTHER_NAMES".
        args (list[Arg], optional): A list of arguments to parse. Defaults to [].
        sources: (list[ArgSource], optional): A list of ArgSource enums or paths that represent sources to source arguments from. Defaults to [ArgSource.cli_args, Path(".env"), ArgSource.envs]. Order decides the priority in which the arguments are sourced. For example if cli_args is before envs then cli_args will have priority over envs.
    """

    prefix: UpperCase = "ATRO_ARGS"
    args: list[Arg] = []
    sources: list[ArgSource | Path] = [ArgSource.cli, Path(".env"), ArgSource.envs]
    _other_name_to_arg: dict[str, Arg] = PrivateAttr({})

    # region Validators
    @model_validator(mode="after")
    def validate_model(self) -> "InputArgs":
        self.validate_sources()
        self.validate_args()
        self.validate_prefix()
        return self

    def validate_sources(self):
        if len(set(self.sources)) != len(self.sources):
            dupes = get_duplicates(self.sources)
            raise ValueError("The elements of list sources must be unique. The following elements are duplicated: " + ", ".join(dupes) + ".")

    def validate_args(self):
        names = [arg.name for arg in self.args] + list(self._other_name_to_arg.keys())
        if len(set(names)) != len(names):
            dupes = get_duplicates(names)
            raise ValueError("Can't have two or more Args with the same name parameter. The following names are duplicated: " + ", ".join(dupes) + ".")

    def validate_prefix(self):
        if self.prefix:
            return

        if ArgSource.envs in self.sources:
            raise ValueError("If ArgSource.envs is in sources then prefix must be provided.")

        for source in self.sources:
            if isinstance(source, Path) and source.suffix == ".env":
                raise ValueError("If a .env file is in sources then prefix must be provided.")

    # endregion

    # region Including sources
    def set_sources(self, sources: list[ArgSource | Path | str]) -> None:
        self.sources = []
        self.include_sources(sources)

    def set_source(self, source: ArgSource | Path | str) -> None:
        self.set_sources([source])

    def include_sources(self, sources: list[ArgSource | Path | str]) -> None:
        for source in sources:
            self.include_source(source)

    def include_source(self, source: ArgSource | Path | str) -> None:
        if isinstance(source, str) and not isinstance(source, ArgSource):
            source = Path(source)
        self.sources.append(source)
        self.validate_sources()

    def include(self, source: ArgSource | Path | str) -> None:
        self.include_source(source)

    # endregion

    # region Adding arguments
    def add_arg(self, arg: Arg) -> None:
        if set(arg.other_names).intersection(set(self._other_name_to_arg.keys())):  # type: ignore
            raise ValueError(f"Can't have two or more Args with the same name parameter. The following names are duplicated: {', '.join(set(arg.other_names).intersection(set(self._other_name_to_arg.keys())))}.")
        for other_name in arg.other_names:
            self._other_name_to_arg[other_name] = arg

        self.args.append(arg)
        self.validate_args()

    def add_args(self, args: Sequence[Arg]) -> None:
        for arg in args:
            self.add_arg(arg)

    def add(self, name: str, other_names: list[str] = [], arg_type: type = str, help: str = "", required: bool = True, default: Any = None):
        self.add_arg(Arg(name=name, other_names=other_names, arg_type=arg_type, help=help, required=required, default=default))
        self.validate_args()

    def add_cls(self, class_type: type) -> None:
        if is_dataclass(class_type):
            self.add_args(add_dataclass(class_type))
        elif issubclass(class_type, BaseModel):
            self.add_args(add_pydantic(class_type))

    # endregion

    # region Get data
    def get_dict(self, cli_input_args: Sequence[str] | None = None) -> dict[str, Any]:
        """Parses the arguments and returns them as a dictionary from (potentially) multiple sources.

        Examples:
            >>> from atro_args import InputArgs, Arg
            >>> input_arg = InputArgs()
            >>> input_arg.add_arg(Arg(name="a", arg_type=float, help="The first addend in the addition."))
            >>> input_arg.get_dict()
            {'a': 1.23}

        Args:
            cli_input_args (Sequence[str]): A list of strings representing the CLI arguments. Defaults to None which means the arguments will be read from sys.argv which is almost always the desired behaviour.

        Returns:
            A dictionary with keys being the argument names and values being the argument values. Argument values will be of the type specified in the Arg model.
        """

        model: dict[str, str] = {}

        for source in self.sources:
            args = load_source(source, self.prefix, self.args, cli_input_args)
            model = merge_dicts(model, args, overwrite=False, current_name=source.value if isinstance(source, ArgSource) else source.as_posix(), updating_dict_name="args")

        model = restrict_keys(model, self.args)
        typed_model = cast_dict_based_on_args(model, self.args)
        typed_model = merge_dicts(typed_model, {arg.name: arg.default for arg in self.args}, overwrite=False, current_name="defaults", updating_dict_name="args")
        throw_if_required_not_populated(typed_model, self.args)

        return typed_model

    def get_cls(self, class_type: type[T], cli_input_args: Sequence[str] | None = None) -> T:
        """Parses the arguments and returns them as an instance of the given class with the data populated from (potentially) multiple sources.

        Examples:
            >>> input_args = InputArgs(prefix="ATRO_TEST")
            >>> input_args.set_source(Path(__file__).parent / ".env")
            >>> resp = input_args.add_cls(TestClassWithUnionType)
            >>> resp = input_args.get_cls(TestClassWithUnionType)
            >>> resp.random_env_file_number
            10

        Args:
            class_type (type): Either a pydantic class or dataclass that we want to populate. Note the arguments have to be added before for this to work, either by .add_cls or by adding arguments one by one.
            cli_input_args (Sequence[str]): A list of strings representing the CLI arguments. Defaults to None which means the arguments will be read from sys.argv which is almost always the desired behaviour.

        Returns:
            Instance of the class provided with the fielids populated from potentially multiple sources.
        """
        typed_dict = self.get_dict(cli_input_args=cli_input_args)

        if is_dataclass(class_type):
            return get_dataclass(typed_dict, class_type, cli_input_args=cli_input_args)
        elif issubclass(class_type, BaseModel):
            return get_pydantic(typed_dict, class_type, cli_input_args=cli_input_args)
        else:
            raise Exception(f"Class type '{class_type}' is not supported.")

    # endregion

    # region Populate data

    def populate_cls(self, class_type: type[T], cli_input_args: Sequence[str] | None = None) -> T:
        """Parses the arguments and returns them as an instance of the given class with the data populated from (potentially) multiple sources.

        Examples:
            >>> input_args = InputArgs(prefix="ATRO_TEST")
            >>> input_args.set_source(Path(__file__).parent / ".env")
            >>> resp = input_args.populate_cls(TestClassWithUnionType)
            >>> resp.random_env_file_number
            10

        Args:
            class_type (type): Either a pydantic class or dataclass that we want to populate.
            cli_input_args (Sequence[str]): A list of strings representing the CLI arguments. Defaults to None which means the arguments will be read from sys.argv which is almost always the desired behaviour.

        Returns:
            Instance of the class provided with the fielids populated from potentially multiple sources.
        """
        self.add_cls(class_type)
        return self.get_cls(class_type, cli_input_args=cli_input_args)

    # endregion
