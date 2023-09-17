import functools
import inspect
from typing import Any, TypeVar

from atro_args.entities.arg_signature import AtroArgSignature
from atro_args.entities.arg_source import SourceType
from atro_args.entities.input_args import InputArgs

T = TypeVar("T")

# region input_args


def input_args(prefix: str | None = None):
    def decorator(func):
        sources = getattr(func, "_sources", [])
        inpt_args = InputArgs(prefix=prefix.upper()) if prefix else InputArgs()
        inpt_args.include_sources(sources)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if hasattr(func, "_sources"):
                delattr(func, "_sources")

            signature_args = list(inspect.signature(func).parameters.values())
            for sig_arg in signature_args:
                atro_arg_sig: AtroArgSignature = sig_arg.default
                atro_arg_sig.name = atro_arg_sig.name or sig_arg.name  # if name not provided infer from signature
                atro_arg_sig.arg_type = atro_arg_sig.arg_type or sig_arg.annotation  # if arg_type not provided infer from signature

                inpt_args.add(name=atro_arg_sig.name, arg_type=atro_arg_sig.arg_type, required=atro_arg_sig.required, default=atro_arg_sig.default)
            kwargs.update(inpt_args.get_dict())

            return func(*args, **kwargs)

        return wrapper

    return decorator


# endregion

# region source


def include_source(source: SourceType):
    def decorator(func):
        sources: list[SourceType] = getattr(func, "_sources", [])
        sources.append(source)
        setattr(func, "_sources", sources)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def set_source(source: SourceType):
    def decorator(func):
        sources: list[SourceType] = getattr(func, "_sources", [])
        sources = [source]
        setattr(func, "_sources", sources)

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def get_arg(name: str | None = None, arg_type: type[T] | None = None, required: bool = True, default: Any = None) -> T:
    # This is lying to the type hinting system, it is a bit of a hack. It does actually get populated by the decorator function further
    # down the line, but the type hinting system doesn't know that.

    return AtroArgSignature(name=name, arg_type=arg_type, required=required, default=default)  # type: ignore


# endregion
