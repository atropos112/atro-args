import ast
import json
import logging


def load_as_py_type_from_string(s, arg_type):
    logging.debug(f"If {s} is str return right away.")
    if arg_type == str:
        return s

    logging.debug(f"If {s} is of simple type (int, float or bool), cast directly and return.")
    if arg_type in [int, float, bool]:
        try:
            return arg_type(s)
        except ValueError:
            raise TypeError(f"Could not load {s} as {arg_type}.")

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

    raise TypeError(f"Could not load {s} as {arg_type}.")
