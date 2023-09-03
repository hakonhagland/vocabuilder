from __future__ import annotations

import logging
import random
import typing

import git
import shutil

from vocabuilder.config import Config
from vocabuilder.constants import TermStatus
from vocabuilder.csv_helpers import CsvDatabaseHeader, CSVwrapper
from vocabuilder.exceptions import DatabaseException
from vocabuilder.mixins import TimeMixin
from vocabuilder.type_aliases import DatabaseRow, DatabaseValue


class Database(TimeMixin):
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
        self.db: dict[str, DatabaseRow] = {}
        self.status = TermStatus()
        self.header = CsvDatabaseHeader()
        self.dbname = self.datadir / self.database_fn
        self.csvwrapper = CSVwrapper(self.dbname)
        self.backupdir = self.datadir / self.backup_dirname
        self.maybe_create_db()
        self.maybe_create_backup_repo()
        self.read_database()
        self.create_backup()
        self.write_cleaned_up()
        self.update_active_vocabulary_info()

    def update_active_vocabulary_info(self) -> None:
        cfg_dir = self.config.get_config_dir()
        active_voca_info_fn_path = cfg_dir / self.active_voca_info_fn
        active_voca_info_fn_path.write_text(self.voca_name, encoding="utf-8")

    def add_item(self, item: DatabaseRow) -> None:
        item[self.header.status] = self.status.NOT_DELETED
        item[self.header.last_modified] = self.epoch_in_seconds()  # epoch
        self.validate_item_content(item)
        db_object = item.copy()
        # NOTE: according to the type hints term1 will have type str | int | None,
        #   but we can be sure that term1 will always be of type str, so we skip
        #   the mypy type check below
        term1 = typing.cast(str, db_object.pop(self.header.term1))
        self.db[term1] = db_object
        self.csvwrapper.append_line(item)
        logging.info("ADDED: " + self.item_to_string(item))

    def assert_term1_exists(self, term1: str) -> None:
        if term1 not in self.db:
            raise DatabaseException(
                f"Unexpected: trying to update non-existent term '{term1}'"
            )

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
        logging.info("Created backup.")

    def delete_item(self, term1: str) -> None:
        if term1 not in self.db:
            raise DatabaseException(f"Term1 '{term1}' does not exist in database")
        item = self.db[term1].copy()
        item[self.header.status] = self.status.DELETED
        item[self.header.term1] = term1
        self.csvwrapper.append_line(item)
        logging.info("DELETED: " + self.item_to_string(item))
        del self.db[term1]

    def get_epoch_diff_in_days(self, t1: int, t2: int) -> int:
        """t1, t2: epoch times. In general these times could be negative, but
        in this application they should always be positive (corresponding to
        dates after year 2022)"""
        if t1 > t2:
            raise DatabaseException(
                "Bad timestamp. Smaller than previous timestamp. Expected larger"
            )
        diff = (t2 - t1) // (24 * 60 * 60)
        return diff

    def get_pairs_exceeding_test_delay(self) -> list[tuple[str, str]]:
        """Get all candidates for a practice session."""
        now = self.epoch_in_seconds()
        keys = self.get_term1_list()
        pairs = []
        for key in keys:
            values = self.db[key]
            last_test = values[self.header.last_test]
            candidate = False
            if last_test is None:
                candidate = True
            else:
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
            raise DatabaseException(
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

    def get_voca_name(self) -> str:
        return self.voca_name

    def item_to_string(self, item: DatabaseRow) -> str:
        return (
            f"term1 = '{item[self.header.term1]}', "
            f"term2 = '{item[self.header.term2]}', "
            f"delay = '{item[self.header.test_delay]}', "
            f"last_test = '{item[self.header.last_test]}', "
            f"last_modified = '{item[self.header.last_modified]}'"
        )

    def maybe_create_backup_repo(self) -> None:
        if self.backupdir.exists():
            if self.backupdir.is_file():
                raise DatabaseException(
                    f"Backup dir {str(self.backupdir)} is a file. Expected directory"
                )
        else:
            self.backupdir.mkdir()
        gitdir = self.backupdir / self.git_dirname
        if gitdir.exists():
            if gitdir.is_file():
                raise DatabaseException(
                    f"Git directory {str(gitdir)} is a file. Expected directory"
                )
        else:
            git.Repo.init(self.backupdir)

    def maybe_create_db(self) -> None:
        if self.dbname.exists():
            if not self.dbname.is_file():
                raise DatabaseException(
                    f"CSV database file {str(self.dbname)} exists "
                    f"but filetype is not file."
                )
        else:
            self.csvwrapper.append_row(
                typing.cast(list[DatabaseValue], self.header.header)
            )  # This will create the file

    def read_database(self) -> None:
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
                    raise DatabaseException(
                        f"Unexpected value for status at line {lineno} in file "
                        f"{self.csvwrapper.filename}"
                    )
        logging.info(f"Read {len(self.db.keys())} lines from database")

    def update_dbfile_item(self, term1: str) -> None:
        """Write the data for db[term1] to the database file"""
        self.db[term1][self.header.last_modified] = self.epoch_in_seconds()  # epoch
        item = self.db[term1].copy()
        item[self.header.term1] = term1
        self.csvwrapper.append_line(item)
        logging.info("UPDATED: " + self.item_to_string(item))

    def update_item(self, term1: str, item: DatabaseRow) -> None:
        self.assert_term1_exists(term1)
        self.db[term1] = item.copy()
        self.update_dbfile_item(term1)

    def update_retest_value(self, term1: str, delay: int) -> None:
        """Set a delay (in days) until next time this term should be practiced"""
        self.assert_term1_exists(term1)
        # NOTE: we can assume that delay is a non-negative integer
        assert delay >= 0
        self.db[term1][self.header.test_delay] = delay
        now = self.epoch_in_seconds()
        self.db[term1][self.header.last_test] = str(now)
        self.update_dbfile_item(term1)

    def validate_item_content(self, item: DatabaseRow) -> None:
        if len(item.keys()) != len(self.header.header):
            raise DatabaseException("unexpected number of elements for item")
        for key in self.header.header:
            if not (key in item):
                raise DatabaseException(f"item missing key '{key}'")
        # header = [status, term1, term2, test_delay, last_test, last_modified]
        for key in item:
            if not isinstance(item[key], self.header.types[key]):
                raise DatabaseException(
                    f"validate_item: the value '{item[key]}' of element {key} has type "
                    f"{type(item[key])}, expected type {self.header.types[key]}"
                )

    def write_cleaned_up(self) -> None:
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
