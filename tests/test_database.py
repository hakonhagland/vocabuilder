from pathlib import Path, PosixPath
import logging
from vocabuilder.vocabuilder import Database
from pytest_mock.plugin import MockerFixture
from _pytest.logging import LogCaptureFixture
#from .fixtures.common import database_object, test_data, data_dir_path


def test_additem(tmp_path: PosixPath, mocker: MockerFixture,
                 test_data: dict, caplog: LogCaptureFixture, database_object: Database,
                 data_dir_path: PosixPath):
    caplog.set_level(logging.INFO)
 
    db = database_object
    assert db.config.datadir_path == data_dir_path
    now = str(db.epoch_in_seconds())
    item = {
        db.header.term1      : "yes",
        db.header.term2      : "네",
        db.header.test_delay : 1,
        db.header.last_test  : now,
    }
    db.add_item(item)
    assert caplog.records[-1].msg.startswith("ADDED: term1 = 'yes'")
