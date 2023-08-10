import re

from vocabuilder.vocabuilder import ConfigException, CsvFileException, DatabaseException


def test_config_exception() -> None:
    try:
        raise ConfigException("Testing")
    except ConfigException as exc:
        msg = str(exc)
        assert re.search(r"Testing", msg)


def test_csvfile_exception() -> None:
    try:
        raise CsvFileException("Testing")
    except CsvFileException as exc:
        msg = str(exc)
        assert re.search(r"Testing", msg)


def test_database_exception() -> None:
    try:
        raise DatabaseException("Testing")
    except DatabaseException as exc:
        msg = str(exc)
        assert re.search(r"Testing", msg)
