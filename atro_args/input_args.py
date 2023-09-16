from collections.abc import Sequence
from dataclasses import is_dataclass
from pathlib import Path
from types import NoneType
from typing import Any, TypeVar, get_args

from annotated_types import UpperCase
from atro_utils import merge_dicts
from pydantic import BaseModel, PrivateAttr, model_validator

from atro_args.arg import Arg
from atro_args.arg_casting import cast_dict_based_on_args
from atro_args.arg_source import ArgSource
from atro_args.arg_source_loading import load_source
from atro_args.helpers import get_duplicates, restrict_keys, throw_if_required_not_populated

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
    sources: list[ArgSource | Path] = [ArgSource.cli_args, Path(".env"), ArgSource.envs]
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
    def set_sources(self, sources: list[ArgSource | Path]) -> None:
        self.sources = []
        self.include_sources(sources)

    def set_source(self, source: ArgSource | Path) -> None:
        self.set_sources([source])

    def include_sources(self, sources: list[ArgSource | Path]) -> None:
        self.sources.extend(sources)
        self.validate_sources()

    def include_source(self, source: ArgSource | Path) -> None:
        self.include_sources([source])

    def include(self, source: ArgSource | Path) -> None:
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

    def add_args(self, args: list[Arg]) -> None:
        for arg in args:
            self.add_arg(arg)
        self.validate_args()

    def add(self, name: str, other_names: list[str] = [], arg_type: type = str, help: str = "", required: bool = True, default: Any = None):
        self.add_arg(Arg(name=name, other_names=other_names, arg_type=arg_type, help=help, required=required, default=default))
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
        if is_dataclass(class_type):
            return self.__get_dataclass(class_type, cli_input_args=cli_input_args)  # type: ignore
        elif issubclass(class_type, BaseModel):
            return self.__get_pydantic(class_type, cli_input_args=cli_input_args)  # type: ignore
        else:
            raise Exception(f"Class type '{class_type}' is not supported.")

    # endregion

    # region popluate

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

    # region "Private" methods

    @staticmethod
    def __account_for_union_type(default_required: bool, possibly_union_type: type | None) -> tuple[bool, type]:
        required = default_required
        arg_type = possibly_union_type

        union_args: tuple[Any, ...] = get_args(possibly_union_type)

        if len(union_args) > 1:
            if not len(get_args(union_args[0])) > 1:
                (arg_type,) = (tp for tp in union_args if tp != NoneType)
            if NoneType in union_args:
                required = False

        if arg_type is None:
            raise Exception("Arg type is None for at least one of the fields, this is not supported.")

        return required, arg_type

    def __add_pydantic(self, pydantic_class_type: type[BaseModel]) -> None:
        for key, val in pydantic_class_type.model_fields.items():
            required, val_type = self.__account_for_union_type(val.is_required(), val.annotation)

            self.add_arg(Arg(name=key, arg_type=val_type, required=required, default=None if str(val.default) == "PydanticUndefined" else val.default))  # type: ignore

        self.validate_args()

    def __add_dataclass(self, dataclass_type: type) -> None:
        for field in dataclass_type.__dataclass_fields__.values():  # type: ignore
            required, val_type = self.__account_for_union_type(True, field.type)

            self.add_arg(Arg(name=field.name, arg_type=val_type, required=required, default=field.default))

    def __get_dataclass(self, dataclass_type: type[T], cli_input_args: Sequence[str] | None = None) -> T:
        if not is_dataclass(dataclass_type):
            raise Exception(f"Developer error: '{dataclass_type}' is not a dataclass and so it shouldn't call __get_dataclass.")
        model_args_required = dataclass_type.__dataclass_fields__

        return self.__get_cls_setup(dataclass_type, model_args_required, cli_input_args=cli_input_args)  # type: ignore

    def __get_pydantic(self, pydantic_class_type: type[T], cli_input_args: Sequence[str] | None = None) -> T:
        if not issubclass(pydantic_class_type, BaseModel):
            raise Exception(f"Developer error: '{pydantic_class_type}' is not a subclass of 'BaseModel' and so it shouldn't call __get_pydantic.")
        model_args_required = pydantic_class_type.model_fields  # type: ignore

        return self.__get_cls_setup(pydantic_class_type, model_args_required, cli_input_args=cli_input_args)

    def __get_cls_setup(self, cls: type[T], model_args_required: dict, cli_input_args: Sequence[str] | None = None) -> T:
        args = self.get_dict(cli_input_args=cli_input_args)
        output_args = {arg: args[arg] for arg in args if arg in model_args_required.keys()}

        # Note the types might be incorret if user error at which point Pydantic will throw an exception.
        myClass: T = cls(**output_args)

        return myClass

    # endregion
