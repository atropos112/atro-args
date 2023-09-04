from dataclasses import dataclass
from pathlib import Path

from pydantic import BaseModel, PositiveInt


@dataclass
class DataTestClass:
    name: str
    surname: str
    age: int
    bozo: bool = False


class PydanticTestClass(BaseModel):
    name: str
    surname: str
    age: PositiveInt
    bozo: bool = False


class PydanticTestClass2(BaseModel):
    random_env_file_number: PositiveInt


class PydanticTestClassWithUnionType(BaseModel):
    random_env_file_number: PositiveInt
    app_env_file_name: Path | None
