from pydantic import BaseModel


class Arg(BaseModel):
    name: str
    other_names: str | list[str] = []
    arg_type: type
    help: str
    required: bool = True
    accept_via_env: bool = True
    accept_via_cli: bool = True
    accept_via_env_file: bool = True
