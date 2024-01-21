import logging
import re
from pathlib import Path
from typing import Callable

import pytest
from _pytest.logging import LogCaptureFixture
from firebase_admin.exceptions import FirebaseError  # type: ignore
from pytest_mock.plugin import MockerFixture

from vocabuilder.constants import TermStatus
from vocabuilder.csv_helpers import CsvDatabaseHeader
from vocabuilder.database import Database
from vocabuilder.exceptions import (
    CsvFileException,
    FirebaseDatabaseException,
    LocalDatabaseException,
    TimeException,
)
from vocabuilder.local_database import LocalDatabase
from vocabuilder.type_aliases import DatabaseRow, DatabaseType

from .common import GetConfig, GetDatabase, PytestDataDict

# from .conftest import database_object, test_data, data_dir_path


class TestAddItem:
    def test_add_ok(self, caplog: LogCaptureFixture, get_database: GetDatabase) -> None:
        db = get_database()
        caplog.set_level(logging.INFO)
        now = db.epoch_in_seconds()
        ldb = db.get_local_database()
        header = ldb.get_header()
        item: DatabaseRow = {
            header.term1: "yes",
            header.term2: "네",
            header.test_delay: 1,
            header.last_test: now,
        }
        db.add_item(item)
        assert caplog.records[-1].msg.startswith("ADDED: term1 = 'yes'")

    def test_extra_item(self, get_database: GetDatabase) -> None:
        """A specific number of keys are required in a DatabaseRow"""
        db = get_database()
        ldb = db.get_local_database()
        now = db.epoch_in_seconds()
        header = ldb.get_header()
        item: DatabaseRow = {
            header.term1: "yes2",
            header.term2: "네2",
            header.test_delay: 1,
            header.last_test: now,
            "xyx": "bad_item",  # extra item will not be accepted
        }
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.add_item(item)
        assert "Unexpected number of elements" in str(excinfo)

    def test_bad_key(self, get_database: GetDatabase) -> None:
        db = get_database()
        now = db.epoch_in_seconds()
        ldb = db.get_local_database()
        header = ldb.get_header()
        item: DatabaseRow = {
            header.term1: "yes3",
            header.term2: "네3",
            header.test_delay: 1,
            "zzz": now,  # bad key
        }
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.add_item(item)
        assert re.search(r"item missing key", str(excinfo))

    def test_bad_type(self, get_database: GetDatabase) -> None:
        db = get_database()
        now = db.epoch_in_seconds()
        ldb = db.get_local_database()
        header = ldb.get_header()
        item: DatabaseRow = {
            header.term1: "yes2",
            header.term2: "네2",
            header.test_delay: "1",  # this value should be of type int not str
            header.last_test: now,
        }
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.add_item(item)
        assert re.search(r"the value '1' of element.*has type", str(excinfo))


class TestBackupRepo:
    def test_create_fail1(
        self,
        setup_database_dir: Callable[[], Path],
        get_config: GetConfig,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.backup_dirname
        filename.touch(exist_ok=False)
        cfg = get_config(setup_firebase=True)
        voca_name = test_data["vocaname"]
        with pytest.raises(LocalDatabaseException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"Expected directory", str(excinfo))

    def test_create_fail2(
        self,
        setup_database_dir: Callable[[], Path],
        get_config: GetConfig,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        backupdir = data_dir / LocalDatabase.backup_dirname
        backupdir.mkdir()
        filename = backupdir / LocalDatabase.git_dirname
        filename.touch(exist_ok=False)
        cfg = get_config()
        voca_name = test_data["vocaname"]
        with pytest.raises(LocalDatabaseException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"Expected directory", str(excinfo))


class TestDataBase:
    # Test specifically push_updated_items_to_firebase()
    @pytest.mark.parametrize(
        "local_db_empty, push_error, value_error, type_error",
        [
            (False, True, False, False),
            (True, False, False, False),
            (False, False, False, False),
            (False, False, True, False),
            (False, False, False, True),
        ],
    )
    def test_create_upd_firebase(
        self,
        local_db_empty: bool,
        push_error: bool,
        value_error: bool,
        type_error: bool,
        caplog: LogCaptureFixture,
        get_config: GetConfig,
        setup_database_dir: Callable[[], Path],
        mocker: MockerFixture,
        test_data: PytestDataDict,
    ) -> None:
        caplog.set_level(logging.INFO)
        cfg = get_config(setup_firebase=True)
        setup_database_dir()
        voca_name = test_data["vocaname"]
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.credentials.Certificate",
            return_value=None,
        )
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.initialize_app",
            return_value=None,
        )
        mock = mocker.MagicMock()
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.db.reference",
            return_value=mock,
        )
        child_mock = mocker.MagicMock()
        mock.child.return_value = child_mock
        header = CsvDatabaseHeader()
        db_dict = {
            "NYJ18uc": {
                header.term1: "apple",
                header.term2: "사과",
                header.test_delay: 1,
                header.last_test: 1684886400,
                header.last_modified: 1677329957,  # local db: 1687329957
                header.status: TermStatus.NOT_DELETED,
            },
            "NYJ18ud": {  # first duplicate item
                header.term1: "apple",
                header.term2: "사과",
                header.test_delay: 1,
                header.last_test: 1684886400,
                header.last_modified: 1677329959,  # local db: 1687329957
                header.status: TermStatus.NOT_DELETED,
            },
            "NYJ18ue": {  # second duplicate item
                header.term1: "apple",
                header.term2: "사과",
                header.test_delay: 1,
                header.last_test: 1684886400,
                header.last_modified: 1677329958,  # local db: 1687329957
                header.status: TermStatus.NOT_DELETED,
            },
        }
        child_mock.get.return_value = db_dict
        if push_error:
            child_mock.push.side_effect = FirebaseError(
                code="code", message="message", http_response=None
            )
        elif value_error:
            child_mock.push.side_effect = ValueError
        elif type_error:
            child_mock.push.side_effect = TypeError
        if local_db_empty:
            mocker.patch(
                "vocabuilder.local_database.LocalDatabase.get_items",
                return_value={},
            )
        mocker.patch(
            "vocabuilder.database.Database.push_updated_items_to_local_database",
            return_value=None,
        )
        db = Database(cfg, voca_name)
        if push_error:
            assert caplog.records[-2].msg.startswith("Firebase: could not push item: ")
        elif value_error:
            assert caplog.records[-2].msg.startswith("Firebase: invalid value error: ")
        elif type_error:
            assert caplog.records[-2].msg.startswith("Firebase: invalid type error: ")
        else:
            assert db is not None

    # Test specifically push_updated_items_to_firebase() and update_item() method
    #   in FireBaseDatabase
    @pytest.mark.parametrize(
        "update_error,value_error,type_error",
        [
            (True, False, False),
            (False, True, False),
            (False, False, True),
        ],
    )
    def test_create_upd_firebase2(
        self,
        update_error: bool,
        value_error: bool,
        type_error: bool,
        caplog: LogCaptureFixture,
        get_config: GetConfig,
        setup_database_dir: Callable[[], Path],
        mocker: MockerFixture,
        test_data: PytestDataDict,
    ) -> None:
        caplog.set_level(logging.INFO)
        cfg = get_config(setup_firebase=True)
        setup_database_dir()
        voca_name = test_data["vocaname"]
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.credentials.Certificate",
            return_value=None,
        )
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.initialize_app",
            return_value=None,
        )
        mock = mocker.MagicMock()
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.db.reference",
            return_value=mock,
        )
        child_mock = mocker.MagicMock()
        mock.child.return_value = child_mock
        header = CsvDatabaseHeader()
        db_dict = {
            "NYJ18uc": {
                header.term1: "apple",
                header.term2: "사과",
                header.test_delay: 1,
                header.last_test: 1684886400,
                header.last_modified: 1677329957,  # local db: 1687329957
                header.status: TermStatus.NOT_DELETED,
            },
        }
        child_mock.get.return_value = db_dict
        child_child_mock = mocker.MagicMock()
        child_mock.child.return_value = child_child_mock
        if update_error:
            child_child_mock.update.side_effect = FirebaseError(
                code="code", message="message", http_response=None
            )
            logging.info(f"child_mock.update = {child_child_mock.update}")
        elif value_error:
            child_child_mock.update.side_effect = ValueError
        elif type_error:
            child_child_mock.update.side_effect = TypeError
        mocker.patch(
            "vocabuilder.database.Database.push_updated_items_to_local_database",
            return_value=None,
        )
        Database(cfg, voca_name)
        if update_error:
            assert caplog.records[-4].msg.startswith(
                "Firebase: could not update item: "
            )
        elif value_error:
            assert caplog.records[-4].msg.startswith("Firebase: invalid value error: ")
        elif type_error:
            assert caplog.records[-4].msg.startswith("Firebase: invalid type error: ")
        else:  # pragma: no cover
            raise Exception("Should not reach here")

    # Test specifically push_updated_items_to_firebase() and update_item() method
    #   in FireBaseDatabase
    def test_create_upd_firebase3(
        self,
        caplog: LogCaptureFixture,
        get_config: GetConfig,
        setup_database_dir: Callable[[], Path],
        mocker: MockerFixture,
        test_data: PytestDataDict,
    ) -> None:
        caplog.set_level(logging.INFO)
        cfg = get_config(setup_firebase=True)
        setup_database_dir()
        voca_name = test_data["vocaname"]
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.credentials.Certificate",
            return_value=None,
        )
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.initialize_app",
            return_value=None,
        )
        mock = mocker.MagicMock()
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.db.reference",
            return_value=mock,
        )
        child_mock = mocker.MagicMock()
        mock.child.return_value = child_mock
        header = CsvDatabaseHeader()
        db_dict: DatabaseType = {
            "NYJ18uc": {
                header.term1: "apple",
                header.term2: "사과",
                header.test_delay: 1,
                header.last_test: 1684886400,
                header.last_modified: 1677329957,  # local db: 1687329957
                header.status: TermStatus.NOT_DELETED,
            },
        }
        child_mock.get.return_value = db_dict
        mocker.patch(
            "vocabuilder.database.Database.push_updated_items_to_local_database",
            return_value=None,
        )
        db = Database(cfg, voca_name)
        db.firebase_database.update_item_same_key("xxxyyy", db_dict["NYJ18uc"])
        assert caplog.records[-1].msg.startswith(
            "Cannot update item: Key 'xxxyyy' not found"
        )

    # Test specifically push_updated_items_to_local_database()
    @pytest.mark.parametrize("assign_items", [False, True])
    def test_create_upd_local(
        self,
        assign_items: bool,
        caplog: LogCaptureFixture,
        get_config: GetConfig,
        setup_database_dir: Callable[[], Path],
        mocker: MockerFixture,
        test_data: PytestDataDict,
    ) -> None:
        caplog.set_level(logging.INFO)
        cfg = get_config(setup_firebase=True)
        setup_database_dir()
        voca_name = test_data["vocaname"]
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.credentials.Certificate",
            return_value=None,
        )
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.initialize_app",
            return_value=None,
        )
        mock = mocker.MagicMock()
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.db.reference",
            return_value=mock,
        )
        child_mock = mocker.MagicMock()
        mock.child.return_value = child_mock
        header = CsvDatabaseHeader()
        db_dict = {
            "NYJ18uc": {
                header.term1: "apple",
                header.term2: "사과",
                header.test_delay: 1,
                header.last_test: 1684886400,
                header.last_modified: 1677329957,  # local db: 1687329957
                header.status: TermStatus.NOT_DELETED,
            },
        }
        if assign_items:
            db_dict["NYJ18ud"] = {  # This item is not in the local database
                header.term1: "apple2",
                header.term2: "사과",
                header.test_delay: 1,
                header.last_test: 1684886400,
                header.last_modified: 1677329959,
                header.status: TermStatus.NOT_DELETED,
            }
            db_dict["NYJ18ue"] = {  # duplicate item
                header.term1: "apple",
                header.term2: "사과",
                header.test_delay: 1,
                header.last_test: 1684886400,
                header.last_modified: 1697329958,  # local db: 1687329957
                header.status: TermStatus.NOT_DELETED,
            }
        child_mock.get.return_value = db_dict
        mocker.patch(
            "vocabuilder.database.Database.push_updated_items_to_firebase",
            return_value=None,
        )
        db = Database(cfg, voca_name)
        assert db is not None
        if assign_items:
            assert caplog.records[-1].msg.startswith("Pushed 2 items to local database")
        else:
            assert caplog.records[-1].msg.startswith(
                "No items pushed to local database"
            )


class TestLocalDatabaseCreate:
    def test_create_fail(
        self,
        setup_database_dir: Callable[[], Path],
        get_config: GetConfig,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.database_fn
        filename.unlink()
        filename.mkdir()
        cfg = get_config()
        voca_name = test_data["vocaname"]
        with pytest.raises(LocalDatabaseException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"filetype is not file", str(excinfo))

    def test_new(
        self,
        setup_database_dir: Callable[[], Path],
        get_config: GetConfig,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.database_fn
        filename.unlink()
        cfg = get_config()
        voca_name = test_data["vocaname"]
        LocalDatabase(cfg, voca_name)
        assert filename.stat().st_size == 52


class TestDeleteItem:
    def test_missing(self, get_database: GetDatabase) -> None:
        db = get_database()
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.delete_item("xyz")
        assert re.search(r"Term1 'xyz' does not exist", str(excinfo))

    def test_missing_fb(self, get_database: GetDatabase) -> None:
        db = get_database()
        with pytest.raises(FirebaseDatabaseException) as excinfo:
            db.firebase_database.delete_item("xyz")
        assert re.search(r"key 'xyz' not found in database", str(excinfo))

    @pytest.mark.parametrize(
        "value_error, no_child, delete_error",
        [
            (False, False, False),
            (True, False, False),
            (False, True, False),
            (False, False, True),
        ],
    )
    def test_fb_delete(
        self,
        value_error: bool,
        no_child: bool,
        delete_error: bool,
        caplog: LogCaptureFixture,
        get_database: GetDatabase,
        mocker: MockerFixture,
    ) -> None:
        db = get_database(init=True)
        caplog.set_level(logging.INFO)
        if value_error:
            db.firebase_database.db.child.side_effect = ValueError
        elif no_child:
            child = db.firebase_database.db.child()
            child.get.return_value = None
        elif delete_error:
            child = db.firebase_database.db.child()
            child.delete.side_effect = FirebaseError(
                code="code", message="message", http_response=None
            )
        db.delete_item("apple")
        if value_error:
            assert caplog.records[-1].msg.startswith(
                "Firebase: delete failed: invalid child path"
            )
        elif no_child:
            assert caplog.records[-1].msg.startswith(
                "Firebase: delete failed: key 'apple' does not exist"
            )
        elif delete_error:
            assert caplog.records[-1].msg.startswith(
                "Firebase: could not delete item: cause: "
                "None, error: code, http_response: None"
            )
        else:
            assert caplog.records[-2].msg.startswith("DELETED: term1 = 'apple'")
            assert caplog.records[-1].msg.startswith("Firebase: deleted item: 'apple'")


class TestEpochDiff:
    day = 24 * 60 * 60

    def test_bad_timestamp(self, get_database: GetDatabase) -> None:
        db = get_database()
        now = db.epoch_in_seconds()
        t2 = now - 1 * self.day
        with pytest.raises(TimeException) as excinfo:
            db.get_epoch_diff_in_days(now, t2)
        assert re.search(r"Bad timestamp", str(excinfo))

    def test_one_day(self, get_database: GetDatabase) -> None:
        db = get_database()
        now = db.epoch_in_seconds()
        t2 = now + 1 * self.day
        assert db.get_epoch_diff_in_days(now, t2) == 1


class TestGetPairs:
    def test_get_all(self, get_database: GetDatabase, mocker: MockerFixture) -> None:
        db = get_database()
        mocker.patch(
            "vocabuilder.mixins.TimeMixin.epoch_in_seconds",
            autospec=True,
            return_value=1687329957,
        )
        pairs = db.get_pairs_exceeding_test_delay()
        assert len(pairs) == 4

    def test_get_single(self, get_database: GetDatabase, mocker: MockerFixture) -> None:
        db = get_database()
        mocker.patch(
            "vocabuilder.local_database.random.randint",
            return_value=3,
        )
        pair = db.get_random_pair()
        assert pair is not None
        assert pair[0] == "apple"

    def test_get_none(self, get_database: GetDatabase, mocker: MockerFixture) -> None:
        db = get_database()
        mocker.patch(
            "vocabuilder.local_database.LocalDatabase.get_pairs_exceeding_test_delay",
            autospec=True,
            return_value=[],
        )
        pair = db.get_random_pair()
        assert pair is None


class TestGetTermData:
    def test_term1_data(self, get_database: GetDatabase) -> None:
        db = get_database()
        row = db.get_term1_data("apple")
        ldb = db.get_local_database()
        header = ldb.get_header()
        assert row[header.term2] == "사과"

    def test_term1_data_bad_key(self, get_database: GetDatabase) -> None:
        db = get_database()
        with pytest.raises(LocalDatabaseException) as excinfo:
            db.get_term1_data("milk")
        assert re.search(r"non-existing", str(excinfo))

    def test_get_term2(self, get_database: GetDatabase) -> None:
        db = get_database()
        term2 = db.get_term2("apple")
        assert term2 == "사과"


class TestOther:
    def test_datadir(self, get_database: GetDatabase, data_dir_path: Path) -> None:
        db = get_database()
        ldb = db.get_local_database()
        assert ldb.config.datadir_path == data_dir_path

    def test_check_term1_exists(self, get_database: GetDatabase) -> None:
        db = get_database()
        assert db.check_term1_exists("apple")


class TestReadDatabase:
    def test_bad_row(
        self,
        setup_database_dir: Callable[[], Path],
        get_config: GetConfig,
        test_data: PytestDataDict,
    ) -> None:
        data_dir = setup_database_dir()
        filename = data_dir / LocalDatabase.database_fn
        with open(filename, "a", encoding="utf_8") as fp:
            fp.write("1, 2, 3")
        cfg = get_config()
        voca_name = test_data["vocaname"]
        with pytest.raises(CsvFileException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"Bad type found", str(excinfo))

    def test_deleted(
        self,
        setup_database_dir: Callable[[], Path],
        get_config: GetConfig,
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
        cfg = get_config()
        voca_name = test_data["vocaname"]
        db = LocalDatabase(cfg, voca_name)
        assert mykey not in db.db

    def test_bad_status(
        self,
        setup_database_dir: Callable[[], Path],
        get_config: GetConfig,
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
        cfg = get_config()
        voca_name = test_data["vocaname"]
        with pytest.raises(LocalDatabaseException) as excinfo:
            LocalDatabase(cfg, voca_name)
        assert re.search(r"Unexpected value for status", str(excinfo))


class TestUpdateDatabase:
    def test_bad_key(self, get_database: GetDatabase) -> None:
        db = get_database()
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
        self,
        caplog: LogCaptureFixture,
        get_database: GetDatabase,
        mocker: MockerFixture,
    ) -> None:
        db = get_database()
        header = CsvDatabaseHeader()
        status = TermStatus()
        row: DatabaseRow = {
            header.status: status.NOT_DELETED,
            header.term2: "사과",
            header.test_delay: 1,
            header.last_test: 1684886400,
            header.last_modified: 1687329957,
        }
        mocker.patch.object(
            db.firebase_database,
            "update_item_same_key",
            return_value=None,
        )
        caplog.set_level(logging.INFO)
        db.update_item("apple", row)
        assert caplog.records[-1].msg.startswith("UPDATED: term1 = 'apple'")

    def test_update_retest(
        self, caplog: LogCaptureFixture, get_database: GetDatabase
    ) -> None:
        db = get_database()
        caplog.set_level(logging.INFO)
        db.update_retest_value("apple", 5)
        assert caplog.records[-1].msg.startswith("UPDATED: term1 = 'apple'")


class TestModifyDatabase:
    def test_bad_key(
        self,
        get_database: GetDatabase,
        mocker: MockerFixture,
        caplog: LogCaptureFixture,
    ) -> None:
        db = get_database()
        header = CsvDatabaseHeader()
        status = TermStatus()
        row: DatabaseRow = {
            header.status: status.NOT_DELETED,
            header.term1: "apple",
            header.term2: "사과",
            header.test_delay: 1,
            header.last_test: 1684886400,
            header.last_modified: 1687329957,
        }
        mocker.patch.object(db.local_database, "delete_item", return_value=None)
        mocker.patch.object(db.local_database, "add_item", return_value=None)
        caplog.set_level(logging.INFO)
        db.modify_item("milk", row)
        assert caplog.records[-1].msg.startswith(
            "Cannot update item: Key 'milk' not found in database"
        )

    def test_success(
        self,
        get_database: GetDatabase,
        mocker: MockerFixture,
        caplog: LogCaptureFixture,
    ) -> None:
        db = get_database(init=True)
        header = CsvDatabaseHeader()
        status = TermStatus()
        row: DatabaseRow = {
            header.status: status.NOT_DELETED,
            header.term1: "milk",
            header.term2: "사과",
            header.test_delay: 1,
            header.last_test: 1684886400,
            header.last_modified: 1687329957,
        }
        mocker.patch.object(db.local_database, "delete_item", return_value=None)
        mocker.patch.object(db.local_database, "add_item", return_value=None)
        caplog.set_level(logging.INFO)
        db.modify_item("apple", row)
        assert caplog.records[-1].msg.startswith(
            "Firebase: renamed item: 'apple' -> 'milk'"
        )
