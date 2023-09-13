import logging
import re
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock.plugin import MockerFixture
from typing import Callable
from vocabuilder.constants import TermStatus
from vocabuilder.csv_helpers import CsvDatabaseHeader
from vocabuilder.exceptions import CsvFileException, LocalDatabaseException
from vocabuilder.type_aliases import DatabaseRow
from vocabuilder.vocabuilder import Config, LocalDatabase
from .common import PytestDataDict

# from .conftest import database_object, test_data, data_dir_path


class TestAddItem:
    def test_add_ok(
        self, caplog: LogCaptureFixture, database_object: LocalDatabase
    ) -> None:
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

    def test_extra_item(self, database_object: LocalDatabase) -> None:
        """A specific number of keys are required in a DatabaseRow"""
        db = database_object
        now = db.epoch_in_seconds()
        item: DatabaseRow = {
            db.header.term1: "yes2",
            db.header.term2: "네2",
            db.header.test_delay: 1,
            db.header.last_test: now,
            "xyx": "bad_item",  # extra item will not be accepted
        }
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.add_item(item)
        assert "unexpected number of elements" in str(excinfo)

    def test_bad_key(self, database_object: LocalDatabase) -> None:
        db = database_object
        now = db.epoch_in_seconds()
        item: DatabaseRow = {
            db.header.term1: "yes3",
            db.header.term2: "네3",
            db.header.test_delay: 1,
            "zzz": now,  # bad key
        }
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.add_item(item)
        assert re.search(r"item missing key", str(excinfo))

    def test_bad_type(self, database_object: LocalDatabase) -> None:
        db = database_object
        now = db.epoch_in_seconds()
        item: DatabaseRow = {
            db.header.term1: "yes2",
            db.header.term2: "네2",
            db.header.test_delay: "1",  # this value should be of type int not str
            db.header.last_test: now,
        }
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.add_item(item)
        assert re.search(r"the value '1' of element.*has type", str(excinfo))


class TestBackupRepo:
    def test_create_fail1(
        self,
        setup_database_dir: Callable[[], Path],
        config_object: Config,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.backup_dirname
        filename.touch(exist_ok=False)
        cfg = config_object
        voca_name = test_data["vocaname"]
        with pytest.raises(LocalDatabaseException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"Expected directory", str(excinfo))

    def test_create_fail2(
        self,
        setup_database_dir: Callable[[], Path],
        config_object: Config,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        backupdir = data_dir / LocalDatabase.backup_dirname
        backupdir.mkdir()
        filename = backupdir / LocalDatabase.git_dirname
        filename.touch(exist_ok=False)
        cfg = config_object
        voca_name = test_data["vocaname"]
        with pytest.raises(LocalDatabaseException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"Expected directory", str(excinfo))


class TestDatabaseCreate:
    def test_create_fail(
        self,
        setup_database_dir: Callable[[], Path],
        config_object: Config,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.database_fn
        filename.unlink()
        filename.mkdir()
        cfg = config_object
        voca_name = test_data["vocaname"]
        with pytest.raises(LocalDatabaseException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"filetype is not file", str(excinfo))

    def test_new(
        self,
        setup_database_dir: Callable[[], Path],
        config_object: Config,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.database_fn
        filename.unlink()
        cfg = config_object
        voca_name = test_data["vocaname"]
        LocalDatabase(cfg, voca_name)
        assert filename.stat().st_size == 52


class TestDeleteItem:
    def test_missing(self, database_object: LocalDatabase) -> None:
        db = database_object
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.delete_item("xyz")
        assert re.search(r"Term1 'xyz' does not exist", str(excinfo))

    def test_success(
        self, caplog: LogCaptureFixture, database_object: LocalDatabase
    ) -> None:
        db = database_object
        caplog.set_level(logging.INFO)
        db.delete_item("apple")
        assert caplog.records[-1].msg.startswith("DELETED: term1 = 'apple'")


class TestEpochDiff:
    day = 24 * 60 * 60

    def test_bad_timestamp(self, database_object: LocalDatabase) -> None:
        db = database_object
        now = db.epoch_in_seconds()
        t2 = now - 1 * self.day
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.get_epoch_diff_in_days(now, t2)
        assert re.search(r"Bad timestamp", str(excinfo))

    def test_one_day(self, database_object: LocalDatabase) -> None:
        db = database_object
        now = db.epoch_in_seconds()
        t2 = now + 1 * self.day
        assert db.get_epoch_diff_in_days(now, t2) == 1


class TestGetPairs:
    def test_get_all(
        self, database_object: LocalDatabase, mocker: MockerFixture
    ) -> None:
        db = database_object
        mocker.patch.object(
            db, "epoch_in_seconds", autospec=True, return_value=1687329957
        )
        pairs = db.get_pairs_exceeding_test_delay()
        assert len(pairs) == 5

    def test_get_single(
        self, database_object: LocalDatabase, mocker: MockerFixture
    ) -> None:
        db = database_object
        mocker.patch(
            "vocabuilder.local_database.random.randint",
            return_value=3,
        )
        pair = db.get_random_pair()
        assert pair is not None
        assert pair[0] == "apple"

    def test_get_none(
        self, database_object: LocalDatabase, mocker: MockerFixture
    ) -> None:
        db = database_object
        mocker.patch.object(
            db, "get_pairs_exceeding_test_delay", autospec=True, return_value=[]
        )
        pair = db.get_random_pair()
        assert pair is None


class TestGetTermData:
    def test_term1_data(self, database_object: LocalDatabase) -> None:
        db = database_object
        row = db.get_term1_data("apple")
        assert row[db.header.term2] == "사과"

    def test_term1_data_bad_key(self, database_object: LocalDatabase) -> None:
        db = database_object
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.get_term1_data("milk")
        assert re.search(r"non-existing", str(excinfo))

    def test_get_term2(self, database_object: LocalDatabase) -> None:
        db = database_object
        term2 = db.get_term2("apple")
        assert term2 == "사과"


class TestOther:
    def test_datadir(self, database_object: LocalDatabase, data_dir_path: Path) -> None:
        db = database_object
        assert db.config.datadir_path == data_dir_path

    def test_check_term1_exists(self, database_object: LocalDatabase) -> None:
        db = database_object
        assert db.check_term1_exists("apple")


class TestReadDatabase:
    def test_bad_row(
        self,
        setup_database_dir: Callable[[], Path],
        config_object: Config,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.database_fn
        with open(filename, "a", encoding="utf_8") as fp:
            fp.write("1, 2, 3")
        cfg = config_object
        voca_name = test_data["vocaname"]
        with pytest.raises(CsvFileException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"Bad type found", str(excinfo))

    def test_deleted(
        self,
        setup_database_dir: Callable[[], Path],
        config_object: Config,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.database_fn
        header = CsvDatabaseHeader()
        status = TermStatus()
        mykey = "apple"
        item = {
            header.status: str(status.DELETED),
            header.term1: mykey,
            header.term2: "사과",
            header.test_delay: "1",
            header.last_test: "1684886400",
            header.last_modified: "1687329957",
        }
        row = [item[key] for key in header.header]
        with open(filename, "a", encoding="utf_8") as fp:
            fp.write(",".join(row))
        cfg = config_object
        voca_name = test_data["vocaname"]
        db = LocalDatabase(cfg, voca_name)
        assert mykey not in db.db

    def test_bad_status(
        self,
        setup_database_dir: Callable[[], Path],
        config_object: Config,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.database_fn
        header = CsvDatabaseHeader()
        mykey = "apple"
        item = {
            header.status: "22",
            header.term1: mykey,
            header.term2: "사과",
            header.test_delay: "1",
            header.last_test: "1684886400",
            header.last_modified: "1687329957",
        }
        row = [item[key] for key in header.header]
        with open(filename, "a", encoding="utf_8") as fp:
            fp.write(",".join(row))
        cfg = config_object
        voca_name = test_data["vocaname"]
        with pytest.raises(LocalDatabaseException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"Unexpected value for status", str(excinfo))


class TestUpdateDatabase:
    def test_bad_key(self, database_object: LocalDatabase) -> None:
        db = database_object
        header = CsvDatabaseHeader()
        status = TermStatus()
        row: DatabaseRow = {
            header.status: status.NOT_DELETED,
            header.term2: "사과",
            header.test_delay: 1,
            header.last_test: 1684886400,
            header.last_modified: 1687329957,
        }
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.update_item("milk", row)
        assert re.search(r"trying to update non-existent term", str(excinfo))

    def test_success(
        self, caplog: LogCaptureFixture, database_object: LocalDatabase
    ) -> None:
        db = database_object
        header = CsvDatabaseHeader()
        status = TermStatus()
        row: DatabaseRow = {
            header.status: status.NOT_DELETED,
            header.term2: "사과",
            header.test_delay: 1,
            header.last_test: 1684886400,
            header.last_modified: 1687329957,
        }
        caplog.set_level(logging.INFO)
        db.update_item("apple", row)
        assert caplog.records[-1].msg.startswith("UPDATED: term1 = 'apple'")

    def test_update_retest(
        self, caplog: LogCaptureFixture, database_object: LocalDatabase
    ) -> None:
        db = database_object
        caplog.set_level(logging.INFO)
        db.update_retest_value("apple", 5)
        assert caplog.records[-1].msg.startswith("UPDATED: term1 = 'apple'")
