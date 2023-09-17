from typing import Any

from pydantic import BaseModel


class AtroArgSignature(BaseModel):
    name: str | None = None
    arg_type: type | None = None
    required: bool = True
    default: Any = None
