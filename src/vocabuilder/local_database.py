from __future__ import annotations

import logging
import random
import typing

import git
import shutil

from vocabuilder.config import Config
from vocabuilder.constants import TermStatus
from vocabuilder.csv_helpers import CsvDatabaseHeader, CSVwrapper
from vocabuilder.exceptions import LocalDatabaseException
from vocabuilder.mixins import TimeMixin
from vocabuilder.type_aliases import DatabaseRow, DatabaseValue, DatabaseType


class LocalDatabase(TimeMixin):
    # NOTE: This is made a class variable since it must be accessible from
    #   pytest before creating an object of this class
    database_fn = "database.csv"
    database_dir = "databases"
    backup_dirname = "backup"
    git_dirname = ".git"
    active_voca_info_fn = "active_db.txt"

    def __init__(self, config: "Config", voca_name: str):
        self.config = config
        self.voca_name = voca_name
        self.datadir = config.get_data_dir() / self.database_dir / voca_name
        self.datadir.mkdir(parents=True, exist_ok=True)
        self.db: DatabaseType = {}
        self.status = TermStatus()
        self.header = CsvDatabaseHeader()
        self.dbname = self.datadir / self.database_fn
        self.csvwrapper = CSVwrapper(self.dbname)
        self.backupdir = self.datadir / self.backup_dirname
        self._maybe_create_db()
        self._maybe_create_backup_repo()
        self._read_database()
        self.create_backup()
        self._write_cleaned_up()
        self._update_active_vocabulary_info()

    # public methods alfabetically sorted below
    # ------------------------------------------

    def add_item(self, item: DatabaseRow) -> None:
        """Add a new item to the database.

        :param item: a dict with the following keys:
        ``header.term1``, ``header.term2``, ``header.test_delay``,
        and ``header.last_test``. Here ``header`` refers to the
        ``CsvDatabaseHeader`` object.

        The ``header.status`` and ``header.last_modified`` keys are added automatically, then
        the dict is pushed to the database
        """
        item[self.header.status] = self.status.NOT_DELETED
        item[self.header.last_modified] = self.epoch_in_seconds()  # epoch
        self._validate_item_content(item)
        db_object = item.copy()
        # NOTE: according to the type hints term1 will have type str | int | None,
        #   but we can be sure that term1 will always be of type str, so we skip
        #   the mypy type check below
        term1 = typing.cast(str, db_object.pop(self.header.term1))
        self.db[term1] = db_object
        self.csvwrapper.append_line(item)
        logging.info("ADDED: " + self._item_to_string(item))

    def assign_item(self, term1: str, item: DatabaseRow) -> None:
        """Replace, add, or delete a new item to the database. The item
        is implicitly deleted if the ``header.status`` key is set to
        ``TermStatus.DELETED``.

        :param item: a dict with the following keys:
        ``header.status``, ``header.term2``,
        ``header.test_delay``, ``header.last_test``, and
        ``header.last_modified``. Here ``header`` refers to the
        ``CsvDatabaseHeader`` object.
        """
        file_obj = item.copy()
        file_obj[self.header.term1] = term1
        self._validate_item_content(file_obj)
        db_object = item.copy()
        self.db[term1] = db_object
        self.csvwrapper.append_line(file_obj)
        logging.info("ASSIGNED: " + self._item_to_string(file_obj))

    def check_term1_exists(self, term1: str) -> bool:
        return term1 in self.db

    def create_backup(self) -> None:
        shutil.copy(str(self.dbname), str(self.backupdir))
        repo = git.Repo(str(self.backupdir))
        index = repo.index
        index.add([self.dbname.name])
        author = git.Actor("vocabuilder", "hakon.hagland@gmail.com")
        committer = author
        index.commit("Startup commit", author=author, committer=committer)
        logging.info(f"Created backup in {self.backupdir}")

    def delete_item(self, term1: str) -> None:
        if term1 not in self.db:
            raise LocalDatabaseException(f"Term1 '{term1}' does not exist in database")
        item = self.db[term1].copy()
        item[self.header.status] = self.status.DELETED
        item[self.header.term1] = term1
        self.csvwrapper.append_line(item)
        logging.info("DELETED: " + self._item_to_string(item))
        del self.db[term1]

    def get_items(self) -> DatabaseType:
        return self.db

    def get_header(self) -> CsvDatabaseHeader:
        return self.header

    def get_pairs_exceeding_test_delay(self) -> list[tuple[str, str]]:
        """Get all candidates for a practice session."""
        now = self.epoch_in_seconds()
        keys = self.get_term1_list()
        pairs = []
        for key in keys:
            values = self.db[key]
            last_test = typing.cast(int, values[self.header.last_test])
            candidate = False
            days_since_last_test = self.get_epoch_diff_in_days(int(last_test), now)
            assert isinstance(values[self.header.test_delay], int)
            # NOTE: cast from type str | int | None -> int
            test_delay = typing.cast(int, values[self.header.test_delay])
            if days_since_last_test >= test_delay:
                candidate = True
            if candidate:
                assert isinstance(self.header.term2, str)
                term2 = typing.cast(str, values[self.header.term2])
                pairs.append((key, term2))
        return pairs

    def get_random_pair(self) -> tuple[str, str] | None:
        pairs = self.get_pairs_exceeding_test_delay()
        if len(pairs) == 0:
            return None
        max = len(pairs) - 1
        min = 0
        idx = random.randint(min, max)
        return pairs[idx]

    def get_term1_data(self, term1: str) -> DatabaseRow:
        if term1 not in self.db:
            raise LocalDatabaseException(
                f"Tried to access non-existing item with key '{term1}'"
            )
        return self.db[term1]

    def get_term1_list(self) -> list[str]:
        return sorted(self.db.keys())

    def get_term2(self, term1: str) -> str:
        row = self.get_term1_data(term1)
        term2 = row[self.header.term2]
        assert isinstance(term2, str)
        return term2

    def get_term2_list(self) -> list[str]:
        return [self.get_term2(term1) for term1 in self.get_term1_list()]

    def get_voca_name(self) -> str:
        return self.voca_name

    def update_item(self, term1: str, item: DatabaseRow) -> None:
        self._assert_term1_exists(term1)
        self.db[term1] = item.copy()
        self._update_dbfile_item(term1)

    def update_retest_value(self, term1: str, delay: int) -> None:
        """Set a delay (in days) until next time this term should be practiced"""
        self._assert_term1_exists(term1)
        # NOTE: we can assume that delay is a non-negative integer
        assert delay >= 0
        self.db[term1][self.header.test_delay] = delay
        self.db[term1][self.header.last_test] = self.epoch_in_seconds()
        self._update_dbfile_item(term1)

    # private methods alfabetically sorted below
    # -------------------------------------------

    def _assert_term1_exists(self, term1: str) -> None:
        if term1 not in self.db:
            raise LocalDatabaseException(
                f"Unexpected: trying to update non-existent term '{term1}'"
            )

    def _item_to_string(self, item: DatabaseRow) -> str:
        return (
            f"term1 = '{item[self.header.term1]}', "
            f"term2 = '{item[self.header.term2]}', "
            f"delay = '{item[self.header.test_delay]}', "
            f"last_test = '{item[self.header.last_test]}', "
            f"last_modified = '{item[self.header.last_modified]}'"
        )

    def _maybe_create_backup_repo(self) -> None:
        if self.backupdir.exists():
            if self.backupdir.is_file():
                raise LocalDatabaseException(
                    f"Backup dir {str(self.backupdir)} is a file. Expected directory"
                )
        else:
            self.backupdir.mkdir()
        gitdir = self.backupdir / self.git_dirname
        if gitdir.exists():
            if gitdir.is_file():
                raise LocalDatabaseException(
                    f"Git directory {str(gitdir)} is a file. Expected directory"
                )
        else:
            git.Repo.init(self.backupdir)

    def _maybe_create_db(self) -> None:
        if self.dbname.exists():
            if not self.dbname.is_file():
                raise LocalDatabaseException(
                    f"CSV database file {str(self.dbname)} exists "
                    f"but filetype is not file."
                )
        else:
            self.csvwrapper.append_row(
                typing.cast(list[DatabaseValue], self.header.header)
            )  # This will create the file

    def _read_database(self) -> None:
        with self.csvwrapper.open_for_read(self.header) as fp:
            for lineno, row in enumerate(fp, start=1):
                # NOTE: It should be impossible (?) that len(row) != len(header) here,
                #  due to the checks in fixup_datatypes() in CSVwrapperReader
                assert len(row) == len(self.header.header)
                status = row[self.header.status]
                term1 = typing.cast(str, row[self.header.term1])
                if status == self.status.NOT_DELETED:
                    self.db[term1] = {
                        self.header.term2: row[self.header.term2],
                        self.header.status: status,
                        self.header.test_delay: row[self.header.test_delay],
                        self.header.last_test: row[self.header.last_test],
                        self.header.last_modified: row[self.header.last_modified],
                    }
                elif status == self.status.DELETED:
                    if term1 in self.db:
                        del self.db[term1]
                else:
                    raise LocalDatabaseException(
                        f"Unexpected value for status at line {lineno} in file "
                        f"{self.csvwrapper.filename}"
                    )
        logging.info(
            f"Read {len(self.db.keys())} lines from local database {self.dbname}"
        )

    def _validate_item_content(self, item: DatabaseRow) -> None:
        """Validate that ``item`` has the correct keys and that the values have the correct
        types. All the keys listed in the ``CsvDatabaseHeader`` object must be present in the
        item.

        :param item: a dict with the keys as defined in the ``CsvDatabaseHeader`` object.
        """
        if len(item.keys()) != len(self.header.header):
            raise LocalDatabaseException(
                f"Unexpected number of elements ({len(item.keys())}) for item. "
                f"Expected {len(self.header.header)} elements. item = {item}"
            )
        for key in self.header.header:
            if not (key in item):
                raise LocalDatabaseException(f"item missing key '{key}'")
        # header = [status, term1, term2, test_delay, last_test, last_modified]
        for key in item:
            if not isinstance(item[key], self.header.types[key]):
                raise LocalDatabaseException(
                    f"validate_item: the value '{item[key]}' of element {key} has type "
                    f"{type(item[key])}, expected type {self.header.types[key]}"
                )

    def _update_active_vocabulary_info(self) -> None:
        cfg_dir = self.config.get_config_dir()
        active_voca_info_fn_path = cfg_dir / self.active_voca_info_fn
        active_voca_info_fn_path.write_text(self.voca_name, encoding="utf-8")

    def _update_dbfile_item(self, term1: str) -> None:
        """Write the data for db[term1] to the database file"""
        self.db[term1][self.header.last_modified] = self.epoch_in_seconds()  # epoch
        item = self.db[term1].copy()
        item[self.header.term1] = term1
        self.csvwrapper.append_line(item)
        logging.info("UPDATED: " + self._item_to_string(item))

    def _write_cleaned_up(self) -> None:
        """
        When a database item is modified it is appended to the database file rather than
        having the whole database rewritten. Of course, this will make the database file
        temporarily contain duplicate items, but this is no problem since the database is read
        sequentially in the read_database() method, and items with larger line number will then
        overwrite items occurring at a lower line number.

        However, database in memory (the self.db dict) does not contain any duplicates
        so this method will remove any duplicates from the database on file
        """
        terms = self.get_term1_list()
        with self.csvwrapper.open_for_write() as fp:
            header = typing.cast(list[DatabaseValue], self.header.header)
            fp.writerow(header)
            for term1 in terms:
                item = self.db[term1].copy()
                item[self.header.term1] = term1
                fp.writeline(item)
        logging.info("Wrote cleaned up version of DB")
