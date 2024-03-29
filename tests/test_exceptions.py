import re

from vocabuilder.exceptions import (
    CommandLineException,
    ConfigException,
    CsvFileException,
    FirebaseDatabaseException,
    LocalDatabaseException,
    SelectVocabularyException,
    TimeException,
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


def test_firebase_database_exception() -> None:
    try:
        raise FirebaseDatabaseException("Testing")
    except FirebaseDatabaseException as exc:
        msg = str(exc)
        assert re.search(r"Testing", msg)


def test_localdatabase_exception() -> None:
    try:
        raise LocalDatabaseException("Testing")
    except LocalDatabaseException as exc:
        msg = str(exc)
        assert re.search(r"Testing", msg)


def test_select_vocabulary_exception() -> None:
    try:
        raise SelectVocabularyException("Testing")
    except SelectVocabularyException as exc:
        msg = str(exc)
        assert re.search(r"Testing", msg)


def test_time_exception() -> None:
    try:
        raise TimeException("Testing")
    except TimeException as exc:
        msg = str(exc)
        assert re.search(r"Testing", msg)
