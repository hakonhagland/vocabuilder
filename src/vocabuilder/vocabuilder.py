#! /usr/bin/env python3
from __future__ import annotations

import configparser
import csv
import importlib.resources  # access non-code resources
import logging
import platform  # determine os name

# import pdb
import random
import shutil
import sys
import time
import typing

from pathlib import Path

from configparser import ConfigParser

# from pprint import pprint
from typing import Callable, Literal, Optional
from types import TracebackType

# NOTE: "Self" type requires python >= 3.11, and we are trying to support python 3.10, so
#   we will work around this using "from __future__ import annotations", see above
#   See also: https://stackoverflow.com/a/33533514/2173773
# from typing_extensions import Self

import git
import platformdirs
from PyQt6 import QtGui
from PyQt6.QtCore import Qt, QCommandLineParser
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
if sys.version_info < MIN_PYTHON:  # pragma: no cover
    sys.exit(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later is required.")


# -----------------
#   Type aliases
# ----------------

DatabaseValue = str | int | None
DatabaseRow = dict[str, DatabaseValue]


# ----------
#   MIXINS
# ----------


class StringMixin:
    """String methods"""

    @staticmethod
    def check_space_or_empty_str(str_: str) -> bool:
        """Is string empty or only space characters?

        :param str str_: Input string
        :return: True if string is empty or only space"""

        if len(str_) == 0 or str_.isspace():
            return True
        return False


class TimeMixin:
    @staticmethod
    def epoch_in_seconds() -> int:
        return int(time.time())


class WarningsMixin:
    @staticmethod
    def display_warning(
        parent: QWidget, msg: str, callback: Callable[[], None] | None = None
    ) -> QMessageBox:
        mbox = QMessageBox(
            parent
        )  # giving "parent" makes the message box appear centered on the parent
        mbox.setIcon(QMessageBox.Icon.Information)
        mbox.setText(msg)
        # mbox.setInformativeText("This is additional information")
        mbox.setWindowTitle("Warning")
        # mbox.setDetailedText("The details are as follows:")
        mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
        mbox.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        if callback is None:

            def button_clicked() -> None:
                WarningsMixin.display_warning_callback(mbox, msg)

            callback = button_clicked
        mbox.open(callback)
        return mbox

    @staticmethod
    def display_warning_callback(
        mbox: QMessageBox, msg: str
    ) -> None:  # pragma: no cover
        """This method is here such that it can be mocked from pytest"""
        pass


# ----------------------
#    Exceptions
# ----------------------


class CommandLineException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Command line exception: {self.value}"


class ConfigException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Config exception: {self.value}"


class CsvFileException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"CSV file exception: {self.value}"


class DatabaseException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Database exception: {self.value}"


class SelectVocabularyException(Exception):
    def __init__(self, value: str):
        self.value = value

    def __str__(self) -> str:
        return f"Select vocabulary exception: {self.value}"


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
        self.open()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        self.button_names = ["&Add", "&Ok", "&Cancel"]
        positions = [(vpos, 0), (vpos, 1), (vpos, 2)]
        callbacks = [
            self.add_button_pressed,
            self.ok_button,
            self.cancel_button,
        ]
        for i, name in enumerate(self.button_names):
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
        items = self.get_db().get_term1_list()
        self.scrollarea.update_items_list(items)
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
        items = self.get_db().get_term1_list()

        def callback(text: str) -> None:
            self.edits[self.header.term1].setText(text)
            self.edits[self.header.term1].setFocus()

        self.scrollarea = QSelectItemScrollArea(items=items, select_callback=callback)
        layout.addWidget(self.scrollarea, vpos, 0, 1, 3)
        return

    def cancel_button(self) -> None:
        self.done(1)

    def get_db(self) -> Database:
        return self.__parent.db

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if (event is not None) and event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
            self.done(1)

    def ok_button(self) -> None:
        if self.add_data():
            self.done(0)

    def update_scroll_area_items(self, text: str) -> None:
        self.scrollarea.update_items(text)


class CommandLineOptions:
    def __init__(self, app: QApplication) -> None:
        app.setApplicationName("VocaBuilder")
        app.setApplicationVersion("0.1")
        parser = QCommandLineParser()
        parser.addHelpOption()
        parser.addVersionOption()
        parser.addPositionalArgument("database", "Database to open")
        parser.process(app)
        arguments = parser.positionalArguments()
        logging.info(f"Commandline database argument: {arguments}")
        num_args = len(arguments)
        if num_args > 1:
            raise CommandLineException(
                "Bad command line arguments. Expected zero or one argument"
            )
        self.database_name: str | None
        if num_args == 1:
            self.database_name = arguments[0]
        else:
            self.database_name = None

    def get_database_name(self) -> str | None:
        return self.database_name


class Config:
    # NOTE: This is made a class variable since it must be accessible from
    #   pytest before creating an object of this class
    dirlock_fn = ".dirlock"
    config_fn = "config.ini"

    def __init__(self) -> None:
        self.appname = "vocabuilder"
        self.lockfile_string = "author=HH"
        self.config_dir = self.check_config_dir()
        self.config_path = Path(self.config_dir) / self.config_fn
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
            with open(str(lock_file), "a", encoding="utf_8") as fp:
                fp.write(self.lockfile_string)
        return path

    def check_correct_config_dir(self, lock_file: Path) -> None:
        """The config dir might be owned by another app with the same name"""
        if lock_file.exists():
            if lock_file.is_file():
                with open(str(lock_file), encoding="utf_8") as fp:
                    line = fp.readline()
                    if line.startswith(self.lockfile_string):
                        return
                msg = "bad content"
            else:
                msg = "is a directory"
        else:
            msg = "missing"
        raise ConfigException(
            f"Unexpected: Config dir lock file: {msg}. "
            f"The data directory {str(lock_file.parent)} might be owned by another app."
        )

    def check_correct_data_dir(self, lock_file: Path) -> None:
        """The data dir might be owned by another app with the same name"""
        if lock_file.exists():
            if lock_file.is_file():
                with open(str(lock_file), encoding="utf_8") as fp:
                    line = fp.readline()
                    if line.startswith(self.lockfile_string):
                        return
                msg = "bad content"
            else:
                msg = "is a directory"
        else:
            msg = "missing"
        raise ConfigException(
            f"Unexpected: Data dir lock file: {msg}. "
            f"The data directory {str(lock_file.parent)} might be owned by another app."
        )

    def get_config_dir(self) -> Path:
        return self.config_dir

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
            with open(str(lock_file), "a", encoding="utf_8") as fp:
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
            with open(str(self.config_path), "w", encoding="utf_8") as _:
                pass  # only create empty file
        config = configparser.ConfigParser()
        self.read_defaults(config)
        config.read(str(self.config_path))
        self.config = config

    def read_defaults(self, config: ConfigParser) -> None:
        path = importlib.resources.files("vocabuilder.data").joinpath(
            "default_config.ini"
        )
        config.read(str(path))


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
        with open(self.filename, "a", newline="", encoding="utf_8") as fp:
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
        self.fp = open(filename, "r", encoding="utf_8")
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
                try:
                    row[key] = self.header.types[key](
                        row[key]
                    )  # cast the element to the correct type
                except TypeError as exc:
                    raise CsvFileException("Bad type found in CSV file") from exc


class CSVwrapperWriter:
    """Context manager for writing lines to the database csv file"""

    def __init__(self, parent: CSVwrapper, filename: str):
        self.parent = parent
        self.fp = open(filename, "w", newline="", encoding="utf_8")
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
    backup_dirname = "backup"
    git_dirname = ".git"

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
        active_voca_info_fn_path = cfg_dir / SelectVocabulary.active_voca_info_fn
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
        # NOTE: this dict is used only for testing purposes
        self.button_names = {names[i]: i for i in range(len(names))}
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
            # NOTE: Theses callbacks usually returns a widget for testing purposes,
            #  The return value is not used when connecting them to the signal below
            callback = typing.cast(Callable[[], None], callbacks[i])
            button.clicked.connect(callback)
            layout.addWidget(button, *positions[i])

    def add_new_entry(self) -> AddWindow:
        return AddWindow(self)

    def backup(self) -> None:
        self.db.create_backup()

    def delete_entry(self) -> QMessageBox:
        mbox = self.display_warning(self, "Delete entry. Not implemented yet")
        return mbox

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        keys = [65, 66, 68, 77, 84, 86, Qt.Key.Key_Escape]  # a, b, d, m, r, v, esc
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
            if (event is not None) and event.key() == key:
                callbacks[i]()

    def modify_entry(self) -> ModifyWindow1:
        return ModifyWindow1(self)

    def quit(self) -> None:
        self.app.quit()

    def run_test(self) -> TestWindow:
        return TestWindow(self)

    def view_entries(self) -> QMessageBox:
        mbox = self.display_warning(self, "View entries. Not implemented yet")
        return mbox


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
        self.open()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        self.button_names = ["&Ok", "&Cancel"]
        positions = [(vpos, 0), (vpos, 2)]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(self.button_names):
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
        items = self.get_db().get_term1_list()

        def callback(text: str) -> None:
            self.edits[self.header.term1].setText(text)

        self.scrollarea = QSelectItemScrollArea(items=items, select_callback=callback)
        layout.addWidget(self.scrollarea, vpos, 0, 1, 4)
        return

    def cancel_button(self) -> None:
        self.done(1)

    def get_db(self) -> Database:
        return self.__parent.db

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if (event is not None) and event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
            self.done(1)

    def modify_item(self) -> bool:
        term1 = self.edits[self.header.term1].text()
        if self.check_space_or_empty_str(term1):
            self.display_warning(self, "Term1 is empty")
            return False
        if not self.get_db().check_term1_exists(term1):
            self.display_warning(self, "Term1 does not exist in database")
            return False
        ModifyWindow2(self, term1, self.__parent.db)
        return True

    def ok_button(self) -> None:
        self.modify_item()

    def update_scroll_area_items(self, text: str) -> None:
        self.scrollarea.update_items(text)


class ModifyWindow2(QDialog, WarningsMixin, StringMixin):
    """Modify/edit the translation of an existing term1 (and/or its translation) and update the
    database.
    """

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
        self.open()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        self.button_names = ["&Ok", "&Cancel"]
        positions = [(vpos, 0), (vpos, 2)]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(self.button_names):
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

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if (event is not None) and event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
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

    def mousePressEvent(self, ev: QMouseEvent | None) -> None:
        if ev is not None:
            if self.clicked_callback is not None:
                self.clicked_callback()
            return super().mousePressEvent(ev)


class QSelectItemScrollArea(QScrollArea):
    def __init__(self, items: list[str], select_callback: Callable[[str], None]):
        super().__init__()
        self.items = items
        self.select_callback = select_callback
        self.scrollwidget = QWidget()
        self.vbox = QVBoxLayout()
        self.vbox.addStretch()  # https://stackoverflow.com/a/63438161/2173773
        self.vbox.setDirection(QBoxLayout.Direction.BottomToTop)
        self.add_items()
        self.scrollwidget.setLayout(self.vbox)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.scrollwidget)
        return

    def add_items(self, match_str: str | None = None) -> None:
        self.labels = []  # This list is used from pytest
        for term in reversed(
            self.items
        ):  # need reverse since vbox has bottom-to-top direction
            if (match_str is None) or (match_str in term):
                label = QLabelClickable(term)
                callback = self.item_clicked(term)
                label.addCallback(callback)
                self.labels.append(label)
                self.vbox.addWidget(label)

    def item_clicked(self, item: str) -> Callable[[], None]:
        def callback() -> None:
            self.select_callback(item)

        return callback

    def update_items(self, text: str) -> None:
        # See: https://stackoverflow.com/a/13103617/2173773
        layout = self.vbox
        for i in reversed(range(layout.count())):
            # layout.itemAt(i).widget().setParent(None)
            layout_item = layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if widget is not None:
                    widget.deleteLater()
        self.add_items(text)
        self.scrollwidget.update()

    def update_items_list(self, items: list[str]) -> None:
        self.items = items


class SelectVocabulary:
    active_voca_info_fn = "active_db.txt"

    def __init__(
        self, opts: CommandLineOptions, cfg: Config, app: QApplication
    ) -> None:
        self.opts = opts
        self.cfg = cfg
        self.app = app
        self.selected_name = None
        self.find_existing_vocabularies()
        database_name = opts.get_database_name()
        if database_name is not None:
            self.selected_name = database_name
        else:
            if not self.read_active_name():
                if not self.choose_most_recent():
                    # app.setQuitOnLastWindowClosed(False)
                    name = self.open_select_voca_window(app)
                    logging.info(f"select voca returned: {name}")
                    # app.setQuitOnLastWindowClosed(True)
                    if name is not None:
                        self.selected_name = name
                    else:
                        logging.info("No vocabulary name found. Exiting..")
                        print("Aborted by user.")
                        quit()

    def choose_most_recent(self) -> bool:
        db_dir = self.cfg.get_data_dir() / Database.database_dir
        current_mtime = 0
        candidate = None
        logging.info("choose most recent..")
        for name in self.existing_vocabularies:
            dbfile = db_dir / name / Database.database_fn
            mtime = dbfile.stat().st_mtime
            if mtime > current_mtime:
                candidate = name
        if candidate is not None:
            self.selected_name = name
            return True
        return False

    def find_existing_vocabularies(self) -> None:
        db_dir = self.cfg.get_data_dir() / Database.database_dir
        self.existing_vocabularies = []
        if db_dir.exists():
            for file in db_dir.iterdir():
                if file.is_dir():
                    dbfile = file / Database.database_fn
                    if dbfile.is_file():
                        self.existing_vocabularies.append(file.name)

    def get_name(self) -> str | None:
        return self.selected_name

    def open_select_voca_window(self, app: QApplication) -> str | None:
        win = SelectNewVocabularyName(self.cfg, self.app)
        win.show()
        self.app.exec()
        return win.name

    def read_active_name(self) -> bool:
        cfg_dir = self.cfg.get_config_dir()
        self.active_voca_info_fn_path = cfg_dir / self.active_voca_info_fn
        if self.active_voca_info_fn_path.is_file():
            txt = self.active_voca_info_fn_path.read_text(encoding="utf-8")
            txt = txt.strip()
            if txt in self.existing_vocabularies:
                self.selected_name = txt
                return True
        return False


class SelectNewVocabularyName(QMainWindow, StringMixin, WarningsMixin):
    def __init__(self, cfg: Config, app: QApplication) -> None:
        super().__init__()
        self.app = app
        self.cfg = cfg
        self.name: str | None = (
            None  # Return value to parent: The name the user selected
        )
        # Prevent self to be destroyed when the close button is clicked
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.button_config = self.cfg.config["Buttons"]
        self.resize(330, 200)
        self.setWindowTitle("Select a vocabulary name")
        layout = QGridLayout()
        vpos = 0
        vpos = self.add_info_label(layout, vpos)
        vpos = self.add_line_edit(layout, vpos)
        vpos = self.add_buttons(layout, vpos)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def add_info_label(self, layout: QGridLayout, vpos: int) -> int:
        label1 = QLabel("No vocabularies found.")
        layout.addWidget(label1, vpos, 0, 1, 2)
        vpos += 1
        label2 = QLabel('Please select a name for a new, e.g. "english-korean"')
        layout.addWidget(label2, vpos, 0, 1, 2)
        vpos += 1
        return vpos

    def add_line_edit(self, layout: QGridLayout, vpos: int) -> int:
        label = QLabel("Vocabulary name: ")
        layout.addWidget(label, vpos, 0)
        self.line_edit = QLineEdit()
        layout.addWidget(self.line_edit, vpos, 1)
        vpos += 1
        return vpos

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        self.button_names = ["&Ok", "&Cancel"]
        positions = [(vpos, 0), (vpos, 1)]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(self.button_names):
            button = QPushButton(name, self)
            self.buttons.append(button)
            button.setMinimumWidth(int(self.button_config["MinWidth"]))
            button.setMinimumHeight(int(self.button_config["MinHeight"]))
            button.clicked.connect(callbacks[i])
            layout.addWidget(button, *positions[i])
        return vpos + 1

    #    def closeEvent(self, event: QCloseEvent):
    #        # do stuff
    #        event.accept()

    def ok_button(self) -> None:
        name = self.line_edit.text()
        if self.check_space_or_empty_str(name):
            self.display_warning(
                self, "Vocabulary name is empty! Please select a valid name"
            )
            return
        else:
            self.name = name
            self.close()
            self.app.exit()

    def cancel_button(self) -> None:
        self.name = None
        self.close()
        self.app.exit()


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
        # NOTE: This complicated approach with callback is mainly done to make it easier
        #  to test the code with pytest
        self.params = TestWindowChooseParameters(parent, self, callback="main_dialog")
        # NOTE: TestWindowChooseParameters will call the callback when finished, i.e. the
        #   main_dialog() method below

    def add_current_term_to_practice(self, layout: QGridLayout, vpos: int) -> int:
        fontsize = self.config.config["FontSize"]["Large"]
        groupbox = QGroupBox("Word/term/phrase to practice")
        grid = QGridLayout()
        label11 = QLabel("Translate this term:")
        grid.addWidget(label11, 0, 0)
        label12 = QLabel(f"{self.lang1_term}")  # type: ignore
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
        self.show_hidden_button = button
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
        # NOTE: This callback is saved as an instance variable to aid pytest
        self.show_hidden_button_callback = self.show_hidden_translation(label32)
        button.clicked.connect(self.show_hidden_button_callback)
        groupbox.setLayout(grid)
        layout.addWidget(groupbox, vpos, 0, 1, 2)
        vpos += 1
        return vpos

    def add_next_done_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.next_button = QPushButton("&Next", self)
        self.next_button.clicked.connect(self.next_button_clicked)
        layout.addWidget(self.next_button, vpos, 0)
        self.done_button = QPushButton("&Done", self)
        self.done_button.clicked.connect(self.done_button_clicked)
        layout.addWidget(self.done_button, vpos, 1)
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
        # NOTE: Buttons and callbacks are saved in these lists to help pytest
        self.retest_buttons: list[QRadioButton] = []
        self.retest_button_callbacks: list[Callable[[], None]] = []
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
        self.retest_buttons.append(radio)
        radio.setChecked(checked)
        callback = self.update_retest_lineedit(edit, str(delay))
        self.retest_button_callbacks.append(callback)
        radio.clicked.connect(callback)
        vpos = i // 3
        hpos = i % 3
        grid.addWidget(radio, vpos + 1, hpos)

    def assign_terms_to_practice(self) -> bool:
        pair = self.__parent.db.get_random_pair()
        if pair is None:
            self.display_warning(self, "No terms ready for practice today!")
            self.done(1)
            return False
        term1, term2 = pair
        self.term1 = term1
        self.term2 = term2
        if self.params.test_direction == TestDirection._1to2:
            self.lang1_term = self.term1
            self.lang2_term = self.term2
        else:
            self.lang1_term = self.term2
            self.lang2_term = self.term1
        return True

    def done_button_clicked(self) -> None:
        delay = self.delay_edit.text()
        self.__parent.db.update_retest_value(self.term1, int(delay))
        self.done(0)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if (event is not None) and event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
            self.done(1)

    def main_dialog(self) -> TestWindow | None:
        if self.params.cancelled:
            return None
        if not self.assign_terms_to_practice():
            return None
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
        self.setWindowTitle("Practice term/phrase/word")
        layout = QGridLayout()
        vpos = 1
        vpos = self.add_param_info_labels(layout, vpos)
        vpos = self.add_current_term_to_practice(layout, vpos)
        vpos = self.add_retest_options(layout, vpos)
        vpos = self.add_next_done_buttons(layout, vpos)
        layout.setRowStretch(layout.rowCount(), 1)
        self.setLayout(layout)
        self.user_edit.setFocus()
        self.open()
        return self

    def next_button_clicked(self) -> None:
        delay = self.delay_edit.text()
        self.__parent.db.update_retest_value(self.term1, int(delay))
        if not self.assign_terms_to_practice():
            return None
        self.term1_label.setText(self.lang1_term)
        self.hidden_label.setText(self.config.config["Practice"]["HiddenText"])
        self.hidden_toggle = True
        self.user_edit.setText("")
        self.user_edit.setFocus()

    def show_hidden_translation(self, label: QLabel) -> Callable[[], None]:
        def callback() -> None:
            if self.hidden_toggle:
                label.setText(self.lang2_term)
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
    def __init__(self, main_window: MainWindow, parent: TestWindow, callback: str):
        super().__init__(main_window)  # make dialog modal
        self.testwin_callback = callback
        self.testwin = parent
        self.config = main_window.config
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
        self.open()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        self.button_names = ["&Ok", "&Cancel"]
        positions = [(vpos, 0), (vpos, 1)]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(self.button_names):
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
        self.choose_from_list_button = checkbox2
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
        self.lang2to1_button = checkbox2
        vbox.addWidget(checkbox2)
        # vbox.addStretch(1)
        groupbox.setLayout(vbox)
        layout.addWidget(groupbox, vpos, 0, 1, 2)
        return vpos + 1

    def cancel_button(self) -> None:
        self.done(1)
        self.cancelled = True
        self.call_parent_callback()

    def call_parent_callback(self) -> None:
        method = getattr(self.testwin, self.testwin_callback)
        # method(self.testwin)
        method()

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
        self.call_parent_callback()


# -------------------
#     Main program
# --------------------


def select_vocabulary(opts: CommandLineOptions, cfg: Config, app: QApplication) -> str:
    """The user can select between different databases with different vocabularies"""
    select = SelectVocabulary(opts, cfg, app)
    name = select.get_name()
    if name is None:
        raise SelectVocabularyException("No vocabulary name given")
    return name


def set_app_options(app: QApplication, cfg: Config) -> None:
    if platform.system() == "Darwin":
        enable = cfg.config.getboolean("MacOS", "EnableAmpersandShortcut")
        QtGui.qt_set_sequence_auto_mnemonic(enable)


def main() -> None:
    # logging.basicConfig(
    #     filename='/tmp/vb.log',
    #     filemode='w',
    #     level=logging.DEBUG,
    # )
    logging.basicConfig(level=logging.DEBUG)
    app = QApplication(sys.argv)
    # options = CommandLineOptions(app)
    cmdline_opts = CommandLineOptions(app)
    config = Config()
    voca_name = select_vocabulary(cmdline_opts, config, app)
    db = Database(config, voca_name)
    set_app_options(app, config)
    window = MainWindow(app, db, config)
    window.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover
    main()
