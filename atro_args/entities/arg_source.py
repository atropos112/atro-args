from enum import StrEnum
from pathlib import Path


class ArgSource(StrEnum):
    """Enum for the non-file source of an argument. This doesn't included sources that are file based.

    Attributes:
        value (str): The value of the enum. Possible choices are "cli" or "envs".
    """

    cli = "cli"
    envs = "envs"


SourceType = ArgSource | Path | str
