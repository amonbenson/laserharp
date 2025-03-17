import os
import logging
from typing import Optional, Any, TypeVar, Literal
from dotenv import load_dotenv
from typing import overload

T = TypeVar("T", str, int, float, bool)


@overload
def getenv(name: str, *, default: Optional[T] = None, type: type[T] = str, required: Literal[True] = True) -> T: ...


@overload
def getenv(name: str, *, default: Optional[T] = None, type: type[T] = str, required: Literal[False] = False) -> Optional[T]: ...


def getenv(name: str, *, default: Any = None, type: type[Any] = str, required: bool = False) -> Optional[Any]:
    # return default value if environment variable is not set
    if name not in os.environ and required:
        raise ValueError(f"Missing required environment variable: {name}")

    # return parsed environment variable
    value = os.getenv(name, default)
    if type == str:
        return str(value)
    elif type == int:
        return int(value)
    elif type == float:
        return float(value)
    elif type == bool:
        return str(value).lower() in ["true", "t", "1", "yes", "y"]
    else:
        raise ValueError(f"Unsupported type: {type}")


def loadenv():
    load_dotenv(".env")
    load_dotenv(".env.local", override=True)

    logging.basicConfig(level=getenv("LH_LOG_LEVEL", default="DEBUG"))


__all__ = ["getenv", "loadenv"]
