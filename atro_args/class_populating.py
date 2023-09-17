from collections.abc import Sequence
from dataclasses import is_dataclass
from types import NoneType
from typing import Any, TypeVar, get_args

from pydantic import BaseModel

from atro_args.entities.arg import Arg

T = TypeVar("T")

# region Add Class


def add_pydantic(pydantic_class_type: type[BaseModel]) -> Sequence[Arg]:
    output = []

    for key, val in pydantic_class_type.model_fields.items():
        required, val_type = account_for_union_type(val.is_required(), val.annotation)

        output.append(Arg(name=key, arg_type=val_type, required=required, default=None if str(val.default) == "PydanticUndefined" else val.default))  # type: ignore

    return output


def add_dataclass(dataclass_type: type) -> Sequence[Arg]:
    output = []

    for field in dataclass_type.__dataclass_fields__.values():  # type: ignore
        required, val_type = account_for_union_type(True, field.type)

        output.append(Arg(name=field.name, arg_type=val_type, required=required, default=field.default))

    return output


# endregion

# region Get Class


def get_dataclass(typed_dict: dict[str, Any], dataclass_type: type[T], cli_input_args: Sequence[str] | None = None) -> T:
    if not is_dataclass(dataclass_type):
        raise Exception(f"Developer error: '{dataclass_type}' is not a dataclass and so it shouldn't call __get_dataclass.")
    model_args_required = dataclass_type.__dataclass_fields__

    return get_cls_setup(typed_dict, dataclass_type, model_args_required, cli_input_args=cli_input_args)  # type: ignore


def get_pydantic(typed_dict: dict[str, Any], pydantic_class_type: type[T], cli_input_args: Sequence[str] | None = None) -> T:
    if not issubclass(pydantic_class_type, BaseModel):
        raise Exception(f"Developer error: '{pydantic_class_type}' is not a subclass of 'BaseModel' and so it shouldn't call __get_pydantic.")
    model_args_required = pydantic_class_type.model_fields  # type: ignore

    return get_cls_setup(typed_dict, pydantic_class_type, model_args_required, cli_input_args=cli_input_args)


# endregion


# region Helpers
def account_for_union_type(default_required: bool, possibly_union_type: type | None) -> tuple[bool, type]:
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


def get_cls_setup(typed_dict: dict[str, Any], cls: type[T], model_args_required: dict, cli_input_args: Sequence[str] | None = None) -> T:
    output_args = {arg: typed_dict[arg] for arg in typed_dict if arg in model_args_required.keys()}

    # Note the types might be incorret if user error at which point Pydantic will throw an exception.
    myClass: T = cls(**output_args)

    return myClass


# endregion
