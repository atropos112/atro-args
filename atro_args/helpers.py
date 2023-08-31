import ast
import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from types import NoneType
from typing import get_args

import yaml


def load_to_py_type(s, arg_type):
    # If type is correct return as is
    if type(s) == arg_type:
        logging.debug(f"{s} is already of type {arg_type} no need to parse.")
        return s

    union_args = get_args(type(s))
    # if its a union type with NoneType, remove the None part and re-run on the first type
    if len(union_args) > 1 and NoneType in union_args:
        (arg_type,) = (arg for arg in union_args if arg != NoneType)
        return load_to_py_type(s, arg_type)

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
                raise ValueError(f"Could not load {s} as {arg_type}.")

    return arg_type(s)


def load_yaml_to_dict(yaml_file: Path) -> dict:
    with open(yaml_file) as file:
        return yaml.safe_load(file)


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    result = dict1.copy()
    result.update(dict2)
    return result


def get_duplicates(lst: list) -> list:
    return list({x for x in lst if lst.count(x) > 1})
