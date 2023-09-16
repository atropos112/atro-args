from typing import Any, _UnionGenericAlias  # type: ignore

from pydantic import BaseModel, ConfigDict


class Arg(BaseModel):
    """Arg is a model that represents a single argument that can be passed to a program via CLI, ENV, ENV file or Yaml file.

    Attributes:
        name (str): The name of the argument. This is the key that will be used to access the value of the argument.
        other_names (list[str], optional): Other names that can be used to access the value of the argument. Defaults to [].
        arg_type (type): The type of the argument. Defaults to str. Possible values are: str, int, float, bool, list, dict, no generic typing allowed, e.g. list[str] is not allowed.
        help (str): The help text for the argument. Defaults to "".
        required (bool, optional): Whether the argument is required. Defaults to True.
        default (Any, optional): The default value of the argument. If set to None it is assumed there is no default (will fail on required=True). Defaults to None.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)
    name: str
    other_names: list[str] = []
    arg_type: type | _UnionGenericAlias = str
    help: str = ""
    required: bool = True
    default: Any = None
