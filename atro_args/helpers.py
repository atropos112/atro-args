import logging
from collections.abc import Sequence
from typing import Any

from atro_args.entities.arg import Arg

# region helpers


def get_duplicates(lst: list) -> list:
    return list({x for x in lst if lst.count(x) > 1})


# Can restrict here also, but do one thing and do that one thing well instead.
def restrict_keys(d: dict[str, str], args: list[Arg]) -> dict[str, str]:
    all_names = [arg.name for arg in args]
    d_copy = d.copy()
    for key in d_copy.keys():
        if key not in all_names:
            d.pop(key)
            logging.warning(f"Key '{key}' is not a valid argument name, as there is no Arg for it. Removing from the dictionary.")

    return d


def throw_if_required_not_populated(d: dict[str, Any], args: Sequence[Arg]) -> None:
    missing_but_required: list[str] = []

    for arg in args:
        if arg.required and d.get(arg.name) is None:
            missing_but_required.append(arg.name)

    if len(missing_but_required) > 0:
        raise KeyError(f"Missing required arguments: '{', '.join(missing_but_required)}'")


# endregion
