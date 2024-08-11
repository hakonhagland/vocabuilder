from typing import Any, ParamSpec, Protocol

from vocabuilder.database import Database
from vocabuilder.vocabuilder import Config

# NOTE: These type aliases cannot start with "Test" because then pytest will
#       believe that they are test classes, see https://stackoverflow.com/q/76689604/2173773

PytestDataDict = dict[str, str]
QtBot = Any  # Missing type hints here
P = ParamSpec("P")


class GetConfig(Protocol):  # pragma: no cover
    def __call__(self, setup_firebase: bool = False) -> Config:
        ...


class GetDatabase(Protocol):  # pragma: no cover
    def __call__(self, init: bool = False) -> Database:
        ...
