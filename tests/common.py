from typing import Any, ParamSpec

# NOTE: These type aliases cannot start with "Test" because then will pytest
#       believe that they are test classes, see https://stackoverflow.com/q/76689604/2173773

PytestDataDict = dict[str, str]
QtBot = Any  # Missing type hints here
P = ParamSpec("P")
