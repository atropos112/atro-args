import ast
import json
import logging
from collections.abc import Mapping, Sequence
from types import NoneType
from typing import Any, TypeVar, get_args

from atro_args.entities.arg import Arg

T = TypeVar("T")


# region casting
def cast_to(s, arg_type: type[T]) -> T:
    # If type is correct return as is
    if type(s) == arg_type:
        logging.debug(f"{s} is already of type {arg_type} no need to parse.")
        return s

    union_args = get_args(type(s))
    # if its a union type with NoneType, remove the None part and re-run on the first type
    if len(union_args) > 1 and NoneType in union_args:
        (arg_type,) = (arg for arg in union_args if arg != NoneType)
        return cast_to(s, arg_type)

    if arg_type in [Mapping, Sequence, list, dict]:
        if not isinstance(s, str):
            raise ValueError(f"Could not load {s} as {arg_type} because it is not clear how to load type {type(s)} into {arg_type}.")

        try:
            logging.debug(f"Trying to load {s} as json.")
            json_loaded = json.loads(s)
            if isinstance(json_loaded, arg_type):
                logging.debug(f"Loaded {s} as json, checking if type is {arg_type} if so returning.")
                return json_loaded
        except json.JSONDecodeError:
            try:
                logging.debug(f"Trying to load {s} as ast, as json.loads failed.")
                ast_loaded = ast.literal_eval(s)
                if isinstance(ast_loaded, arg_type):
                    logging.debug(f"Loaded {s} using ast, checking if type is {arg_type} if so returning.")
                    return ast_loaded
            except (ValueError, SyntaxError):
                raise TypeError(f"Could not load {s} as {arg_type}.")

    try:
        output = arg_type(s)
    except (ValueError, SyntaxError):
        raise TypeError(f"Could not load {s} as {arg_type}.")

    return output


def cast_dict_based_on_args(model: dict[str, str], args: Sequence[Arg]) -> dict[str, Any]:
    for arg in args:
        if arg.name in model:
            model[arg.name] = cast_to(model[arg.name], arg.arg_type)
    return model


#  endregion
