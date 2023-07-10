#! /usr/bin/env python3
from __future__ import annotations

import configparser
import csv
import logging

# import pdb
import random
import shutil
import sys
import time
import typing

from pathlib import Path

# from pprint import pprint
from typing import Callable, Literal, Optional
from types import TracebackType

# NOTE: "Self" type requires python >= 3.11, and we are trying to support python 3.10, so
#   we will work around this using "from __future__ import annotations", see above
#   See also: https://stackoverflow.com/a/33533514/2173773
# from typing_extensions import Self

import git
import platformdirs
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator, QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QApplication,
    QBoxLayout,
    QDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)


# NOTE: type hints for collection of builtin types requires python>=3.9, see
#  https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
# NOTE: type hints using union types (using pipe only), e.g. "str | None",
#   requires python >= 3.10
#   see: https://docs.python.org/3/library/stdtypes.html#types-union
MIN_PYTHON = (3, 10)
if sys.version_info < MIN_PYTHON:
    sys.exit(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later is required.")


# -----------------
#   Type aliases
# ----------------

DatabaseValue = str | int | None
DatabaseRow = dict[str, DatabaseValue]

#   MIXINS
# ----------


class StringMixin:
    @staticmethod
    def check_space_or_empty_str(str_: str) -> bool:
        if len(str_) == 0 or str_.isspace():
            return True
        return False


class TimeMixin:
    @staticmethod
    def epoch_in_seconds() -> int:
        return int(time.time())


class WarningsMixin:
    @staticmethod
    def display_warning(parent: QWidget, msg: str) -> None:
        mbox = QMessageBox(
            parent
        )  # "parent" makes the message box appear centered on the parent
        mbox.setIcon(QMessageBox.Icon.Information)
        mbox.setText(msg)
        # mbox.setInformativeText("This is additional information")
        mbox.setWindowTitle("Warning")
        # mbox.setDetailedText("The details are as follows:")
        mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
        mbox.exec()


# ----------------------
#    Exceptions
# ----------------------


class ConfigException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Config exception: {self.value}"


class DatabaseException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Database exception: {self.value}"


# -----------------------------
#   CLASSES (alphabetically)
# -----------------------------


class AddWindow(QDialog, WarningsMixin, StringMixin, TimeMixin):
    """Add a new term (and its translation) to the database, then ask for a another term to add.
    Continue the above procedure of adding terms until the user clicks the cancel button
    """

    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)  # make dialog modal
        # NOTE: using double underscore "__parent" to avoid confilict with "parent"
        #      method in a parent class
        self.__parent = parent
        self.config = parent.config
        self.header = CsvDatabaseHeader()
        self.window_config = self.config.config["AddWindow"]
        self.button_config = self.config.config["Buttons"]
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
        self.setWindowTitle("Add new item")
        layout = QGridLayout()
        vpos = 0
        self.add_scroll_area(layout, vpos)
        vpos += 1
        self.edits: dict[str, QLineEdit] = {}  # mypy requires type annotation here
        vpos = self.add_line_edits(layout, vpos)
        self.add_buttons(layout, vpos)
        self.setLayout(layout)
        self.exec()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        names = ["&Add", "&Ok", "&Cancel"]
        positions = [(vpos, 0), (vpos, 1), (vpos, 2)]
        callbacks = [
            self.add_button_pressed,
            self.ok_button,
            self.cancel_button,
        ]

        for i, name in enumerate(names):
            button = QPushButton(name, self)
            self.buttons.append(button)
            button.setMinimumWidth(int(self.button_config["MinWidth"]))
            button.setMinimumHeight(int(self.button_config["MinHeight"]))
            button.clicked.connect(callbacks[i])
            layout.addWidget(button, *positions[i])
        return vpos + 1

    def add_button_pressed(self) -> None:
        self.add_data()
        self.edits[self.header.term1].setText("")
        self.edits[self.header.term2].setText("")
        self.edits[self.header.test_delay].setText("")
        self.edits[self.header.term1].setFocus()

    def add_data(self) -> bool:
        term1 = self.edits[self.header.term1].text()
        if self.check_space_or_empty_str(term1):
            self.display_warning(self, "Term1 is empty")
            return False
        if self.__parent.db.check_term1_exists(term1):
            self.display_warning(self, "Term1 already exists in database")
            return False
        term2 = self.edits[self.header.term2].text()
        if self.check_space_or_empty_str(term2):
            self.display_warning(self, "Term2 is empty")
            return False
        delay_str = self.edits[self.header.test_delay].text()
        if len(delay_str) == 0:
            delay = 0
        else:
            delay = int(delay_str)
        now = self.epoch_in_seconds()
        item: DatabaseRow = {
            self.header.term1: term1,
            self.header.term2: term2,
            self.header.test_delay: delay,
            self.header.last_test: now,
        }
        self.__parent.db.add_item(item)
        return True

    def add_line_edits(self, layout: QGridLayout, vpos: int) -> int:
        large = self.config.config["FontSize"]["Large"]
        descriptions = ["Term1:", "Term2:", "Retest in x days:"]
        fontsizes = [large, large, None]
        names = [self.header.term1, self.header.term2, self.header.test_delay]
        callbacks = [self.update_scroll_area_items, None, None]
        for i, desc in enumerate(descriptions):
            label = QLabel(desc)
            layout.addWidget(label, vpos, 0)
            edit = QLineEdit(self)
            if fontsizes[i] is not None:
                edit.setStyleSheet(f"QLineEdit {{font-size: {fontsizes[i]};}}")
            if callbacks[i] is not None:
                edit.textChanged.connect(callbacks[i])  # type: ignore
            self.edits[names[i]] = edit
            layout.addWidget(edit, vpos, 1, 1, 2)
            vpos += 1
        validator = QIntValidator()
        validator.setBottom(0)
        self.edits[self.header.test_delay].setValidator(validator)
        self.edits[self.header.test_delay].setText("0")
        return vpos

    def add_scroll_area(self, layout: QGridLayout, vpos: int) -> None:
        # NOTE: using double underscore "__scroll" to avoid confilict with "scroll"
        #      method in a parent class
        self.__scroll = QScrollArea()
        self.scrollwidget = QWidget()
        self.vbox = QVBoxLayout()
        self.vbox.addStretch()  # https://stackoverflow.com/a/63438161/2173773
        self.vbox.setDirection(QBoxLayout.Direction.BottomToTop)
        self.add_scroll_area_items(self.vbox)
        self.scrollwidget.setLayout(self.vbox)
        self.__scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.__scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.__scroll.setWidgetResizable(True)
        self.__scroll.setWidget(self.scrollwidget)
        layout.addWidget(self.__scroll, vpos, 0, 1, 3)
        return

    def add_scroll_area_items(self, vbox: QVBoxLayout, text: str | None = None) -> None:
        terms = self.__parent.db.get_term1_list()
        for term in reversed(
            terms
        ):  # need reverse since vbox has bottom-to-top direction
            if (text is None) or (text in term):
                object = QLabel(term)
                vbox.addWidget(object)

    def cancel_button(self) -> None:
        self.done(1)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if event.key() == 16777216:  # "ESC" pressed
            self.done(1)

    def ok_button(self) -> None:
        if self.add_data():
            self.done(0)

    def update_scroll_area_items(self, text: str) -> None:
        # See: https://stackoverflow.com/a/13103617/2173773
        layout = self.vbox
        for i in reversed(range(layout.count())):
            # layout.itemAt(i).widget().setParent(None)
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.add_scroll_area_items(self.vbox, text)
        # self.scrollwidget.setLayout(self.vbox)
        self.scrollwidget.update()


class Config:
    # NOTE: This is made a class variable since it must be accessible from
    #   pytest before creating an object of this class
    dirlock_fn = ".dirlock"

    def __init__(self) -> None:
        self.appname = "vocabuilder"
        self.lockfile_string = "author=HH"
        self.config_dir = self.check_config_dir()
        self.config_path = Path(self.config_dir) / "config.ini"
        self.read_config()
        self.datadir_path = self.get_data_dir_path()

    def check_config_dir(self) -> Path:
        config_dir = platformdirs.user_config_dir(appname=self.appname)
        path = Path(config_dir)
        lock_file = path / self.dirlock_fn
        if path.exists():
            if path.is_file():
                raise ConfigException(
                    f"Config directory {str(path)} is file. Expected directory"
                )
            self.check_correct_config_dir(lock_file)
        else:
            path.mkdir(parents=True)
            with open(str(lock_file), "a") as fp:
                fp.write(self.lockfile_string)
        return path

    def check_correct_config_dir(self, lock_file: Path) -> None:
        """The config dir might be owned by another app with the same name"""
        if lock_file.is_file():
            with open(str(lock_file)) as fp:
                line = fp.readline()
                if line.startswith(self.lockfile_string):
                    return
        raise ConfigException(
            f"Config dir lock file missing. "
            f"The data directory {str(lock_file.parent)} might be owned by another app."
        )

    def check_correct_data_dir(self, lock_file: Path) -> None:
        """The data dir might be owned by another app with the same name"""
        if lock_file.is_file():
            with open(str(lock_file)) as fp:
                line = fp.readline()
                if line.startswith(self.lockfile_string):
                    return
        raise ConfigException(
            f"Data dir lock file missing. "
            f"The data directory {str(lock_file.parent)} might be owned by another app."
        )

    def get_config_dir(self) -> Path:
        return self.config_path

    def get_data_dir(self) -> Path:
        return self.datadir_path

    def get_data_dir_path(self) -> Path:
        data_dir = platformdirs.user_data_dir(appname=self.appname)
        path = Path(data_dir)
        lock_file = path / self.dirlock_fn
        if path.exists():
            if path.is_file():
                raise ConfigException(
                    f"Data directory {str(path)} is file. Expected directory"
                )
            self.check_correct_data_dir(lock_file)
        else:
            path.mkdir(parents=True)
            with open(str(lock_file), "a") as fp:
                fp.write(self.lockfile_string)
        return path

    def read_config(self) -> None:
        path = Path(self.config_path)
        if path.exists():
            if not path.is_file():
                raise ConfigException(
                    f"Config filename {str(path)} exists, but filetype is not file"
                )
        else:
            with open(str(self.config_path), "w") as _:
                pass  # only create empty file
        config = configparser.ConfigParser()
        defaults = {
            "AddWindow": {
                "Width": 400,
                "Height": 400,
            },
            "Buttons": {
                "MinWidth": 50,
                "MinHeight": 30,
            },
            "FontColor": {
                "Blue": "blue",
                "Red": "red",
            },
            "FontSize": {
                "Small": "10px",
                "Large": "18px",
            },
            "ModifyWindow1": {
                "Width": "400",
                "Height": "400",
            },
            "ModifyWindow2": {
                "Width": "400",
                "Height": "400",
            },
            "Practice": {
                "HiddenText": "<Hidden>",
            },
            "TestWindow": {
                "Width": "400",
                "Height": "400",
            },
        }
        config.read_dict(defaults)  # type: ignore
        config.read(str(self.config_path))
        self.config = config


class CsvDatabaseHeader:
    """
    status        : 0 = The item has been deleted, 1, 2, 3,.. the item is not deleted
    term1         : "From" term
    term2         : "To" term (translation of Term1)
    test_delay    : Number of days to next possible test, 0 or negative means no delay
    last_test     : timestamp (epoch) of last time this term was practiced
    last_modified : timestamp (epoch) of last time any of the previous was modified
    """

    status = "Status"
    term1 = "Term1"
    term2 = "Term2"
    test_delay = "TestDelay"
    last_test = "LastTest"
    last_modified = "LastModified"
    header = [status, term1, term2, test_delay, last_test, last_modified]
    types = {
        status: int,
        term1: str,
        term2: str,
        test_delay: int,
        last_test: int,
        last_modified: int,
    }


class CSVwrapper:
    def __init__(self, dbname: Path):
        self.quotechar = '"'
        self.delimiter = ","
        self.filename = str(dbname)
        self.header = CsvDatabaseHeader()

    def append_line(self, row_dict: DatabaseRow) -> None:
        row = self.dict_to_row(row_dict)
        self.append_row(row)

    def append_row(self, row: list[DatabaseValue]) -> None:
        with open(self.filename, "a", newline="") as fp:
            csvwriter = csv.writer(
                fp,
                delimiter=self.delimiter,
                quotechar=self.quotechar,
                quoting=csv.QUOTE_MINIMAL,
            )
            csvwriter.writerow(row)

    def dict_to_row(self, row_dict: DatabaseRow) -> list[DatabaseValue]:
        row = []
        for key in self.header.header:
            row.append(row_dict[key])
        return row

    def open_for_read(self, header: CsvDatabaseHeader) -> "CSVwrapperReader":
        return CSVwrapperReader(self, self.filename, header)

    def open_for_write(self) -> "CSVwrapperWriter":
        return CSVwrapperWriter(self, self.filename)


class CSVwrapperReader:
    """Context manager for reading lines from the database csv file"""

    def __init__(self, parent: CSVwrapper, filename: str, header: CsvDatabaseHeader):
        self.parent = parent
        self.header = header
        self.fp = open(filename, "r")
        self.csvh = csv.DictReader(
            self.fp,
            delimiter=self.parent.delimiter,
            quotechar=self.parent.quotechar,
        )

    def __enter__(self) -> CSVwrapperReader:
        return self

    def __exit__(
        self,
        type: Optional[type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        self.fp.close()
        return False  # TODO: handle exceptions

    def __iter__(self, start: int = 0) -> CSVwrapperReader:
        return self

    def __next__(self) -> dict[str, DatabaseValue]:
        try:
            row = next(self.csvh)
        except StopIteration as e:
            raise e
        self.fixup_datatypes(row)
        return row

    def fixup_datatypes(self, row: dict[str, str]) -> None:
        """NOTE: this method modifies the input argument 'row'"""
        for key in row:
            value = row[key]
            if value == "NA":
                row[key] = None  # type: ignore
            else:
                row[key] = self.header.types[key](
                    row[key]
                )  # cast the element to the correct type


class CSVwrapperWriter:
    """Context manager for writing lines to the database csv file"""

    def __init__(self, parent: CSVwrapper, filename: str):
        self.parent = parent
        self.fp = open(filename, "w", newline="")
        self.csvwriter = csv.writer(
            self.fp,
            delimiter=self.parent.delimiter,
            quotechar=self.parent.quotechar,
            quoting=csv.QUOTE_MINIMAL,
        )

    def __enter__(self) -> CSVwrapperWriter:
        return self

    def __exit__(
        self,
        type: Optional[type[BaseException]],
        value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> Literal[False]:
        self.fp.close()
        return False  # TODO: handle exceptions

    def fixup_none_datavalues(self, row: list[DatabaseValue]) -> None:
        """NOTE: This method is modifying the input argument 'row'"""
        for i, item in enumerate(row):
            if item is None:
                row[i] = "NA"

    def writerow(self, row: list[DatabaseValue]) -> None:
        self.fixup_none_datavalues(row)
        self.csvwriter.writerow(row)

    def writeline(self, row_dict: DatabaseRow) -> None:
        row = self.parent.dict_to_row(row_dict)
        self.fixup_none_datavalues(row)
        self.csvwriter.writerow(row)


class Database(TimeMixin):
    # NOTE: This is made a class variable since it must be accessible from
    #   pytest before creating an object of this class
    database_fn = "database.csv"
    database_dir = "databases"

    def __init__(self, config: "Config", voca_name: str):
        self.config = config
        self.datadir = config.get_data_dir() / self.database_dir / voca_name
        self.datadir.mkdir(parents=True, exist_ok=True)
        self.db: dict[str, DatabaseRow] = {}
        self.status = TermStatus()
        self.header = CsvDatabaseHeader()
        self.dbname = self.datadir / self.database_fn
        self.csvwrapper = CSVwrapper(self.dbname)
        self.backupdir = self.datadir / "backup"
        self.maybe_create_db()
        self.maybe_create_backup_repo()
        self.read_database()
        self.create_backup()
        self.write_cleaned_up()

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
        item = self.db[term1].copy()
        item[self.header.status] = self.status.DELETED
        item[self.header.term1] = term1
        self.csvwrapper.append_line(item)
        logging.info("DELETED: " + self.item_to_string(item))
        del self.db[term1]

    def get_epoch_diff_in_days(self, t1: int, t2: int) -> int:
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
        return self.db[term1]

    def get_term1_list(self) -> list[str]:
        return sorted(self.db.keys())

    def get_term2(self, term1: str) -> str:
        term2 = self.db[term1][self.header.term2]
        assert isinstance(term2, str)
        return term2

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
        gitdir = self.backupdir / ".git"
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
                if len(row) != len(self.header.header):
                    raise DatabaseException(
                        f"Currupt database {self.csvwrapper.filename}? Line {lineno} : "
                        f"Expected {len(self.header.header)} items, "
                        f"got {len(row)} items"
                    )
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
        self.db[term1] = item.copy()
        self.update_dbfile_item(term1)

    def update_retest_value(self, term1: str, delay: str) -> None:
        """Set a delay (in days) until next time this term should be practiced"""
        self.db[term1][self.header.test_delay] = int(delay)
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
        """When a database item is modified it is appended to the database file rather than
        having the whole database rewritten. Of course, this will make the database file
        temporarily contain duplicate items, but this is no problem since the database is read
        sequentially in the read_database() method, and items with larger line number will then
        overwrite items occurring at a lower line number.
           However, the database in memory (the self.db dict) does not contain any duplicates
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


class MainWindow(QMainWindow, WarningsMixin):
    def __init__(self, app: QApplication, db: Database, config: "Config"):
        super().__init__()
        self.config = config
        self.button_config = self.config.config["Buttons"]
        self.app = app
        self.db = db
        self.resize(330, 200)
        self.setWindowTitle("VocaBuilder")
        layout = QGridLayout()
        self.add_buttons(layout)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def add_buttons(self, layout: QGridLayout) -> None:
        self.buttons = []
        names = ["Add", "Modify", "Test", "Delete", "View", "Backup"]
        positions = [(0, 0), (0, 1), (0, 2), (1, 0), (1, 1), (1, 2)]
        callbacks = [
            self.add_new_entry,
            self.modify_entry,
            self.run_test,
            self.delete_entry,
            self.view_entries,
            self.backup,
        ]

        for i, name in enumerate(names):
            button = QPushButton(name, self)
            button.setSizePolicy(QSizePolicy.Policy.Ignored, QSizePolicy.Policy.Ignored)
            self.buttons.append(button)
            button.setMinimumWidth(int(self.button_config["MinWidth"]))
            button.setMinimumHeight(int(self.button_config["MinHeight"]))
            button.clicked.connect(callbacks[i])
            layout.addWidget(button, *positions[i])

    def add_new_entry(self) -> None:
        AddWindow(self)

    def backup(self) -> None:
        self.db.create_backup()

    def delete_entry(self) -> None:
        self.display_warning(self, "Delete entry. Not implemented yet")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        keys = [65, 66, 68, 77, 84, 86, 16777216]  # a, b, d, m, r, v, esc
        callbacks = [
            self.add_new_entry,
            self.backup,
            self.delete_entry,
            self.modify_entry,
            self.run_test,
            self.view_entries,
            self.quit,
        ]
        for i, key in enumerate(keys):
            if event.key() == key:
                callbacks[i]()

    def modify_entry(self) -> None:
        ModifyWindow1(self)

    def quit(self) -> None:
        self.app.quit()

    def run_test(self) -> None:
        TestWindow(self)

    def view_entries(self) -> None:
        self.display_warning(self, "View entries. Not implemented yet")


class ModifyWindow1(QDialog, WarningsMixin, StringMixin):
    """Modify/edit the translation of an existing term1 (and/or its translation) and update the
    database. Then, ask for a another term to modify. Continue the above
    procedure of modifying terms until the user clicks the cancel button"""

    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)  # make dialog modal
        # NOTE: using double underscore "__parent" to avoid confilict with "parent"
        #      method in a parent class
        self.__parent = parent
        self.config = parent.config
        self.header = CsvDatabaseHeader()
        self.button_config = self.config.config["Buttons"]
        self.window_config = self.config.config["ModifyWindow1"]
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
        self.setWindowTitle("Choose item to modify")
        self.edits: dict[str, QLineEdit] = {}
        layout = QGridLayout()
        vpos = 0
        self.add_scroll_area(layout, vpos)
        vpos += 1
        vpos = self.add_line_edit(layout, vpos)
        self.add_buttons(layout, vpos)
        self.setLayout(layout)
        self.exec()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        names = ["&Ok", "&Cancel"]
        positions = [(vpos, 0), (vpos, 2)]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(names):
            button = QPushButton(name, self)
            self.buttons.append(button)
            button.setMinimumWidth(int(self.button_config["MinWidth"]))
            button.setMinimumHeight(int(self.button_config["MinHeight"]))
            button.clicked.connect(callbacks[i])
            layout.addWidget(button, *positions[i], 1, 2)
        return vpos + 1

    def add_line_edit(self, layout: QGridLayout, vpos: int) -> int:
        large = self.config.config["FontSize"]["Large"]
        descriptions = ["Term1:"]
        fontsizes = [large]
        names = [self.header.term1]
        callbacks = [self.update_scroll_area_items]
        for i, desc in enumerate(descriptions):
            label = QLabel(desc)
            layout.addWidget(label, vpos, 0)
            edit = QLineEdit(self)
            if fontsizes[i] is not None:
                edit.setStyleSheet(f"QLineEdit {{font-size: {fontsizes[i]};}}")
            if callbacks[i] is not None:
                edit.textChanged.connect(callbacks[i])
            self.edits[names[i]] = edit
            layout.addWidget(edit, vpos, 1, 1, 3)
            vpos += 1
        return vpos

    def add_scroll_area(self, layout: QGridLayout, vpos: int) -> None:
        # NOTE: using double underscore "__scroll" to avoid confilict with "scroll"
        #      method in a parent class
        self.__scroll = QScrollArea()
        self.scrollwidget = QWidget()
        self.vbox = QVBoxLayout()
        self.vbox.addStretch()  # https://stackoverflow.com/a/63438161/2173773
        self.vbox.setDirection(QBoxLayout.Direction.BottomToTop)
        self.add_scroll_area_items(self.vbox)
        self.scrollwidget.setLayout(self.vbox)
        self.__scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.__scroll.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.__scroll.setWidgetResizable(True)
        self.__scroll.setWidget(self.scrollwidget)
        layout.addWidget(self.__scroll, vpos, 0, 1, 4)
        return

    def add_scroll_area_items(self, vbox: QVBoxLayout, text: str | None = None) -> None:
        terms = self.__parent.db.get_term1_list()
        for term in reversed(
            terms
        ):  # need reverse since vbox has bottom-to-top direction
            if (text is None) or (text in term):
                label = QLabelClickable(term)
                label.addCallback(self.scroll_area_item_clicked(term))
                vbox.addWidget(label)

    def cancel_button(self) -> None:
        self.done(1)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if event.key() == 16777216:  # "ESC" pressed
            self.done(1)

    def modify_item(self) -> bool:
        term1 = self.edits[self.header.term1].text()
        if self.check_space_or_empty_str(term1):
            self.display_warning(self, "Term1 is empty")
            return False
        if not self.__parent.db.check_term1_exists(term1):
            self.display_warning(self, "Term1 does not exist in database")
            return False
        ModifyWindow2(self, term1, self.__parent.db)
        return True

    def ok_button(self) -> None:
        self.modify_item()

    def scroll_area_item_clicked(self, item: str) -> Callable[[], None]:
        def callback() -> None:
            self.edits[self.header.term1].setText(item)

        return callback

    def update_scroll_area_items(self, text: str) -> None:
        # See: https://stackoverflow.com/a/13103617/2173773
        layout = self.vbox
        for i in reversed(range(layout.count())):
            # layout.itemAt(i).widget().setParent(None)
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.add_scroll_area_items(self.vbox, text)
        # self.scrollwidget.setLayout(self.vbox)
        self.scrollwidget.update()


class ModifyWindow2(QDialog, WarningsMixin, StringMixin):
    """Modify/edit the translation of an existing term1 (and/or its translation) and update the
    database."""

    def __init__(self, parent: ModifyWindow1, term1: str, database: Database):
        super().__init__(parent)  # make dialog modal
        # NOTE: using double underscore "__parent" to avoid confilict with "parent"
        #      method in a parent class
        self.__parent = parent
        self.term1 = term1
        self.db = database
        self.header = CsvDatabaseHeader()
        self.term2 = self.db.get_term2(self.term1)
        self.config = self.__parent.config
        self.button_config = self.config.config["Buttons"]
        self.window_config = self.config.config["ModifyWindow2"]
        # NOTE: resize(.., -1) means: let QT figure out the optimal height of the window
        self.resize(int(self.window_config["Width"]), -1)
        self.setWindowTitle("Modify item")
        layout = QGridLayout()
        self.edits: dict[str, QLineEdit] = {}
        vpos = 0
        vpos = self.add_labels(layout, vpos)
        vpos = self.add_line_edits(layout, vpos)
        self.add_buttons(layout, vpos)
        self.setLayout(layout)
        self.exec()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        names = ["&Ok", "&Cancel"]
        positions = [(vpos, 0), (vpos, 2)]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(names):
            button = QPushButton(name, self)
            self.buttons.append(button)
            button.setMinimumWidth(int(self.button_config["MinWidth"]))
            button.setMinimumHeight(int(self.button_config["MinHeight"]))
            button.clicked.connect(callbacks[i])
            layout.addWidget(button, *positions[i], 1, 2)
        return vpos + 1

    def add_labels(self, layout: QGridLayout, vpos: int) -> int:
        label11 = QLabel("Current term1:")
        layout.addWidget(label11, vpos, 0, 1, 1)
        label12 = QLabel(self.term1)
        large = self.config.config["FontSize"]["Large"]
        term1_color = self.config.config["FontColor"]["Blue"]
        label12.setStyleSheet(f"QLabel {{font-size: {large}; color: {term1_color}; }}")
        layout.addWidget(label12, vpos, 1, 1, 3)
        vpos += 1
        label21 = QLabel("Current term2:")
        layout.addWidget(label21, vpos, 0, 1, 1)
        label22 = QLabel(self.term2)
        term2_color = self.config.config["FontColor"]["Red"]
        label22.setStyleSheet(f"QLabel {{font-size: {large}; color: {term2_color}; }}")
        layout.addWidget(label22, vpos, 1, 1, 3)
        vpos += 1
        return vpos

    def add_line_edits(self, layout: QGridLayout, vpos: int) -> int:
        large = self.config.config["FontSize"]["Large"]
        descriptions = ["New term1:", "New term2:"]
        fontsizes = [large, large]
        edittexts = [self.term1, self.term2]
        names = [self.header.term1, self.header.term2]
        for i, desc in enumerate(descriptions):
            label = QLabel(desc)
            layout.addWidget(label, vpos, 0)
            edit = QLineEdit(self)
            if fontsizes[i] is not None:
                edit.setStyleSheet(f"QLineEdit {{font-size: {fontsizes[i]};}}")
            self.edits[names[i]] = edit
            edit.setText(edittexts[i])
            layout.addWidget(edit, vpos, 1, 1, 3)
            vpos += 1
        return vpos

    def cancel_button(self) -> None:
        self.done(1)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if event.key() == 16777216:  # "ESC" pressed
            self.done(1)

    def modify_item(self) -> bool:
        old_term1 = self.term1
        new_term1 = self.edits[self.header.term1].text()
        new_term2 = self.edits[self.header.term2].text()
        if self.check_space_or_empty_str(new_term1):
            self.display_warning(self, "Term1 is empty")
            return False
        if self.check_space_or_empty_str(new_term2):
            self.display_warning(self, "Term2 is empty")
            return False
        item = self.db.get_term1_data(old_term1).copy()
        if new_term1 == old_term1:
            item[self.header.term2] = new_term2
            self.db.update_item(new_term1, item)
        else:
            item[self.header.term1] = new_term1
            item[self.header.term2] = new_term2
            self.db.delete_item(old_term1)
            self.db.add_item(item)
        return True

    def ok_button(self) -> None:
        if self.modify_item():
            self.done(0)


class QLabelClickable(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)
        self.clicked_callback: Callable[[], None] | None = None

    def addCallback(self, callback: Callable[[], None] | None) -> None:
        self.clicked_callback = callback

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if self.clicked_callback is not None:
            self.clicked_callback()
        return super().mousePressEvent(ev)


class SelectVocabulary:
    def __init__(self) -> None:
        self.selected_name = "english-korean"

    def get_name(self) -> str:
        return self.selected_name


class TermStatus:
    """Has this term been deleted from the database?"""

    DELETED = 0
    NOT_DELETED = 1


class TestDirection:
    """When running a practice/test session, should you practice translating words
    from language 1 to language 2, or practice translating words from language 2
    to language 1?
    """

    _1to2 = 1
    _2to1 = 2


class TestMethod:
    """When running a practice/test session, should the words to be practiced be
    picked at random, or should the user select the words from a list?"""

    Random = 1
    List = 2


class TestWindow(QDialog, WarningsMixin):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)  # make dialog modal
        # NOTE: using double underscore "__parent" to avoid confilict with "parent"
        #      method in a parent class
        self.__parent = parent
        self.config = parent.config
        self.window_config = self.config.config["TestWindow"]
        self.params = TestWindowChooseParameters(parent)
        if self.params.cancelled:
            return
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
        self.setWindowTitle("Practice term/phrase/word")
        layout = QGridLayout()
        vpos = 1
        vpos = self.add_param_info_labels(layout, vpos)
        pair = self.__parent.db.get_random_pair()
        if pair is None:
            self.display_warning(self, "No terms ready for practice today!")
            self.done(1)
        else:
            term1, term2 = pair
            self.term1 = term1
            self.term2 = term2
            vpos = self.add_current_term_to_practice(layout, vpos, term1)
            vpos = self.add_retest_options(layout, vpos)
            vpos = self.add_next_done_buttons(layout, vpos)
            layout.setRowStretch(layout.rowCount(), 1)
            self.setLayout(layout)
            self.user_edit.setFocus()
            self.exec()

    def add_current_term_to_practice(
        self, layout: QGridLayout, vpos: int, term1: str
    ) -> int:
        fontsize = self.config.config["FontSize"]["Large"]
        groupbox = QGroupBox("Word/term/phrase to practice")
        grid = QGridLayout()
        label11 = QLabel("Translate this term:")
        grid.addWidget(label11, 0, 0)
        label12 = QLabel(f"{term1}")
        self.term1_label = label12
        term1_color = self.config.config["FontColor"]["Blue"]
        label12.setStyleSheet(
            f"QLabel {{font-size: {fontsize}; color: {term1_color}; }}"
        )
        grid.addWidget(label12, 0, 1)
        label21 = QLabel("Type translation here:")
        grid.addWidget(label21, 1, 0)
        edit = QLineEdit(self)
        edit.setStyleSheet(f"QLineEdit {{font-size: {fontsize};}}")
        self.user_edit = edit
        grid.addWidget(edit, 1, 1)
        button = QPushButton("&Show translation: ", self)
        grid.addWidget(button, 2, 0)
        self.hidden_text_placeholder = self.config.config["Practice"]["HiddenText"]
        label32 = QLabel(self.hidden_text_placeholder)
        # In case you want to copy/paste the label text:
        label32.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.hidden_label = label32
        self.hidden_toggle = True  # True means: text is hidden
        term2_color = self.config.config["FontColor"]["Red"]
        label32.setStyleSheet(
            f"QLabel {{font-size: {fontsize}; color: {term2_color}; }}"
        )
        grid.addWidget(label32, 2, 1)
        button.clicked.connect(self.show_hidden_translation(label32))
        groupbox.setLayout(grid)
        layout.addWidget(groupbox, vpos, 0, 1, 2)
        vpos += 1
        return vpos

    def add_next_done_buttons(self, layout: QGridLayout, vpos: int) -> int:
        next_button = QPushButton("&Next", self)
        next_button.clicked.connect(self.next_button_clicked)
        layout.addWidget(next_button, vpos, 0)
        done_button = QPushButton("&Done", self)
        done_button.clicked.connect(self.done_button_clicked)
        layout.addWidget(done_button, vpos, 1)
        return vpos + 1

    def add_param_info_labels(self, layout: QGridLayout, vpos: int) -> int:
        if self.params.test_direction == TestDirection._1to2:
            lang1 = 1
            lang2 = 2
        else:
            lang1 = 2
            lang2 = 1
        groupbox = QGroupBox("Parameters")
        grid = QGridLayout()
        label11 = QLabel("<i>Direction:</i>")
        label11.setStyleSheet("QLabel {color: #ffb84d}")
        grid.addWidget(label11, 0, 0)
        label12 = QLabel(f"{lang1} -> {lang2}")
        grid.addWidget(label12, 0, 1)
        if self.params.test_method == TestMethod.Random:
            ttype = "Random"
        else:
            ttype = "Choose"
        label21 = QLabel("<i>Choose type:</i>")
        label21.setStyleSheet("QLabel {color: #ffb84d}")
        grid.addWidget(label21, 1, 0)
        label22 = QLabel(f"{ttype}")
        grid.addWidget(label22, 1, 1)
        groupbox.setLayout(grid)
        layout.addWidget(groupbox, vpos, 0, 1, 2)
        return vpos + 1

    def add_retest_options(self, layout: QGridLayout, vpos: int) -> int:
        groupbox = QGroupBox("When to practice this word again?")
        grid = QGridLayout()
        label11 = QLabel("<i>Practice this word again after x days:</i>")
        label11.setStyleSheet("QLabel {color: #ffb84d}")
        grid.addWidget(label11, 0, 0, 1, 2)
        edit = QLineEdit(self)
        self.delay_edit = edit
        edit.setText("1")
        validator = QIntValidator()
        validator.setBottom(0)
        edit.setValidator(validator)
        # edit.setStyleSheet(f"QLineEdit {{font-size: {fontsize};}}")
        grid.addWidget(edit, 0, 2)
        for i, delay in enumerate([0, 1, 3, 7, 30]):
            checked = False
            if delay == 1:
                checked = True
            self.add_retest_radio_button(grid, i, delay, checked, edit)
        groupbox.setLayout(grid)
        layout.addWidget(groupbox, vpos, 0, 1, 2)
        return vpos + 1

    def add_retest_radio_button(
        self,
        grid: QGridLayout,
        i: int,
        delay: int,
        checked: bool,
        edit: QLineEdit,
    ) -> None:
        day_str = "days"
        if delay == 1:
            day_str = "day"
        radio = QRadioButton(f"{delay} {day_str}")
        radio.setChecked(checked)
        radio.clicked.connect(self.update_retest_lineedit(edit, str(delay)))
        vpos = i // 3
        hpos = i % 3
        grid.addWidget(radio, vpos + 1, hpos)

    def done_button_clicked(self) -> None:
        delay = self.delay_edit.text()
        self.__parent.db.update_retest_value(self.term1, delay)
        self.done(0)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if event.key() == 16777216:  # "ESC" pressed
            self.done(1)

    def next_button_clicked(self) -> None:
        delay = self.delay_edit.text()
        self.__parent.db.update_retest_value(self.term1, delay)
        pair = self.__parent.db.get_random_pair()
        if pair is None:
            self.display_warning(self, "No more terms ready for practice today!")
            self.done(1)
        else:
            term1, term2 = pair
            self.term1 = term1
            self.term2 = term2
            self.term1_label.setText(term1)
            self.hidden_label.setText(self.config.config["Practice"]["HiddenText"])
            self.user_edit.setText("")
            self.user_edit.setFocus()

    def show_hidden_translation(self, label: QLabel) -> Callable[[], None]:
        def callback() -> None:
            if self.hidden_toggle:
                label.setText(self.term2)
                self.hidden_toggle = False
            else:
                label.setText(self.hidden_text_placeholder)
                self.hidden_toggle = True

        return callback

    def update_retest_lineedit(self, edit: QLineEdit, delay: str) -> Callable[[], None]:
        def callback() -> None:
            edit.setText(delay)

        return callback


class TestWindowChooseParameters(QDialog):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)  # make dialog modal
        self.config = parent.config
        self.button_config = self.config.config["Buttons"]
        self.cancelled = False
        self.resize(350, 250)
        self.setWindowTitle("Specify practice session parameters")
        layout = QGridLayout()
        vpos = 0
        vpos = self.add_check_box_group1(layout, vpos)
        vpos = self.add_check_box_group2(layout, vpos)
        # vpos = self.add_line_edits(layout, vpos)
        vpos = self.add_buttons(layout, vpos)
        self.setLayout(layout)
        self.exec()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        names = ["Ok", "Cancel"]
        positions = [(vpos, 0), (vpos, 1)]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(names):
            button = QPushButton(name, self)
            self.buttons.append(button)
            button.setMinimumWidth(int(self.button_config["MinWidth"]))
            button.setMinimumHeight(int(self.button_config["MinHeight"]))
            button.clicked.connect(callbacks[i])
            layout.addWidget(button, *positions[i])
        return vpos + 1

    def add_check_box_group1(self, layout: QGridLayout, vpos: int) -> int:
        groupbox = QGroupBox("How to select the word to practice?")
        vbox = QVBoxLayout()
        checkbox1 = QRadioButton("Random")
        self.random_button = checkbox1
        checkbox1.setChecked(True)
        vbox.addWidget(checkbox1)
        checkbox2 = QRadioButton("Choose word from list")
        checkbox2.setChecked(False)
        vbox.addWidget(checkbox2)
        # vbox.addStretch(1)
        groupbox.setLayout(vbox)
        layout.addWidget(groupbox, vpos, 0, 1, 2)
        return vpos + 1

    def add_check_box_group2(self, layout: QGridLayout, vpos: int) -> int:
        groupbox = QGroupBox("Choose direction of translation to practice")
        vbox = QVBoxLayout()
        checkbox1 = QRadioButton("From language 1 to 2")
        checkbox1.setChecked(True)
        self.lang1to2_button = checkbox1
        vbox.addWidget(checkbox1)
        checkbox2 = QRadioButton("From language 2 to 1")
        checkbox2.setChecked(False)
        vbox.addWidget(checkbox2)
        # vbox.addStretch(1)
        groupbox.setLayout(vbox)
        layout.addWidget(groupbox, vpos, 0, 1, 2)
        return vpos + 1

    def cancel_button(self) -> None:
        self.done(1)
        self.cancelled = True

    def ok_button(self) -> None:
        if self.random_button.isChecked():
            self.test_method = TestMethod.Random
        else:
            self.test_method = TestMethod.List
        if self.lang1to2_button.isChecked():
            self.test_direction = TestDirection._1to2
        else:
            self.test_direction = TestDirection._2to1
        self.done(0)
        self.cancelled = False


# -------------------
#     Main program
# --------------------


def select_vocabulary() -> str:
    """The user can select between different databases with different vocabularies"""
    select = SelectVocabulary()
    return select.get_name()


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    config = Config()
    voca_name = select_vocabulary()
    db = Database(config, voca_name)
    app = QApplication(sys.argv)
    window = MainWindow(app, db, config)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
