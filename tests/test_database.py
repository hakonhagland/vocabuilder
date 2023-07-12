import logging
import re
from pathlib import PosixPath

import pytest
from _pytest.logging import LogCaptureFixture

from vocabuilder.vocabuilder import Database, DatabaseException, DatabaseRow

# from .conftest import database_object, test_data, data_dir_path


def test_additem(caplog: LogCaptureFixture, database_object: Database) -> None:
    db = database_object
    caplog.set_level(logging.INFO)
    now = db.epoch_in_seconds()
    item: DatabaseRow = {
        db.header.term1: "yes",
        db.header.term2: "네",
        db.header.test_delay: 1,
        db.header.last_test: now,
    }
    db.add_item(item)
    assert caplog.records[-1].msg.startswith("ADDED: term1 = 'yes'")


def test_additem_bad(database_object: Database) -> None:
    db = database_object
    now = db.epoch_in_seconds()
    item: DatabaseRow = {
        db.header.term1: "yes2",
        db.header.term2: "네2",
        db.header.test_delay: 1,
        db.header.last_test: now,
        "xyx": "bad_item",
    }
    with pytest.raises(DatabaseException) as excinfo:
        db.add_item(item)
    assert "unexpected number of elements" in str(excinfo)


def test_additem_bad_type(database_object: Database) -> None:
    db = database_object
    now = db.epoch_in_seconds()
    item: DatabaseRow = {
        db.header.term1: "yes2",
        db.header.term2: "네2",
        db.header.test_delay: "1",  # this value should be of type int not str
        db.header.last_test: now,
    }
    with pytest.raises(DatabaseException) as excinfo:
        db.add_item(item)
    assert re.search(r"the value '1' of element.*has type", str(excinfo))


def test_datadir(database_object: Database, data_dir_path: PosixPath) -> None:
    db = database_object
    assert db.config.datadir_path == data_dir_path
