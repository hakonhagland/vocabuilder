import re

from vocabuilder.vocabuilder import (
    CommandLineException,
    ConfigException,
    CsvFileException,
    DatabaseException,
    SelectVocabularyException,
)


def test_commandline_exception() -> None:
    try:
        raise CommandLineException("Testing")
    except CommandLineException as exc:
        msg = str(exc)
        assert re.search(r"Testing", msg)


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


def test_select_vocabulary_exception() -> None:
    try:
        raise SelectVocabularyException("Testing")
    except SelectVocabularyException as exc:
        msg = str(exc)
        assert re.search(r"Testing", msg)
