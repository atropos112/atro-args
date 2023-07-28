import ast
import json
import logging
from collections.abc import Mapping, Sequence


def load_to_py_type(s, arg_type):
    # If type is correct return as is
    if type(s) == arg_type:
        logging.debug(f"{s} is already of type {arg_type} no need to parse.")
        return s

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
