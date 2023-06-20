#! /usr/bin/env python3

from PyQt6 import QtGui
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QDialog, QWidget, QPushButton, QGridLayout, QSizePolicy
from PyQt6.QtWidgets import QMainWindow, QScrollArea, QLabel, QVBoxLayout, QLineEdit, QBoxLayout
from PyQt6.QtWidgets import QMessageBox, QGroupBox, QCheckBox, QRadioButton
from PyQt6.QtGui import QIntValidator, QFont, QKeyEvent, QMouseEvent

import configparser
import csv
import datetime
import git
import logging
import os
import pdb
import random
import shutil
import sys
from typing import Callable, Type

# type hints for collection of builtin types requires python>=3.9, see
#  https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
MIN_PYTHON = (3, 9)
if sys.version_info < MIN_PYTHON:
    sys.exit(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later is required.")

logging.basicConfig(level=logging.INFO)


#----------
#   MIXINS
#----------

class DateMixin():
    def today_as_string(self):
        return datetime.datetime.now().strftime(self.config.datefmt_str)


class StringMixin():
    @staticmethod
    def check_space_or_empty_str(str_: str) -> bool:
        if len(str_) == 0 or str_.isspace():
            return True
        return False


class WarningsMixin():
    @staticmethod
    def display_warning(parent, msg: str) -> None:
        mbox = QMessageBox(parent)  # "parent" makes the message box appear centered on the parent
        mbox.setIcon(QMessageBox.Icon.Information)
        mbox.setText(msg)
        #mbox.setInformativeText("This is additional information")
        mbox.setWindowTitle("Warning")
        #mbox.setDetailedText("The details are as follows:")
        mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
        mbox.exec()


#----------------------
#    Exceptions
#----------------------

class DatabaseException(Exception):
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return f"Database exception: {self.value}"


#-----------------------------
#   CLASSES (alphabetically)
#-----------------------------

class AddWindow(QDialog, WarningsMixin, DateMixin, StringMixin):
    """Add a new term (and its translation) to the database, then ask for a another term to add.
    Continue the above procedure of adding terms until the user clicks the cancel button"""
    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)  # make dialog modal
        self.parent = parent
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
        vpos = self.add_line_edits(layout, vpos)
        self.add_buttons(layout, vpos)
        self.setLayout(layout)
        #widget = QWidget()
        ##widget.setLayout(layout)
        #self.setCentralWidget(widget)
        self.exec()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> None:
        self.buttons = []
        names = ['&Add', '&Ok', '&Cancel']
        positions = [(vpos, 0), (vpos, 1), (vpos, 2) ]
        callbacks = [self.add_button_pressed, self.ok_button, self.cancel_button]

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
            self.display_warning(self, 'Term1 is empty')
            return False
        if self.parent.db.check_term1_exists(term1):
            self.display_warning(self, 'Term1 already exists in database')
            return False
        term2 = self.edits[self.header.term2].text()
        if self.check_space_or_empty_str(term2):
            self.display_warning(self, 'Term2 is empty')
            return False
        delay = self.edits[self.header.test_delay].text()
        if len(delay) == 0:
            delay = "0"
        today = self.today_as_string()
        item = {
                    self.header.term1      : term1,
                    self.header.term2      : term2,
                    self.header.test_delay : delay,
                    self.header.last_test  : today,
                  }
        self.parent.db.add_item(item)
        return True

    def add_line_edits(self, layout: QGridLayout, vpos: int):
        large = self.config.config["FontSize"]["Large"]
        self.edits = {}
        descriptions = ['Term1:', 'Term2:', 'Retest in x days:']
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
                edit.textChanged.connect(callbacks[i])
            self.edits[names[i]] = edit
            layout.addWidget(edit, vpos, 1, 1, 2)
            vpos += 1
        validator = QIntValidator()
        validator.setBottom(0)
        self.edits[self.header.test_delay].setValidator(validator)
        self.edits[self.header.test_delay].setText("0")
        return vpos

    def add_scroll_area(self, layout: QGridLayout, vpos: int) -> None:
        self.scroll = QScrollArea()
        self.scrollwidget = QWidget()
        self.vbox = QVBoxLayout()
        self.vbox.addStretch()  # https://stackoverflow.com/a/63438161/2173773
        self.vbox.setDirection(QBoxLayout.Direction.BottomToTop)
        self.add_scroll_area_items(self.vbox)
        self.scrollwidget.setLayout(self.vbox)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scrollwidget)
        layout.addWidget(self.scroll, vpos, 0, 1, 3)
        return

    def add_scroll_area_items(self, vbox: QVBoxLayout, text=None) -> None:
        terms = self.parent.db.get_term1_list()
        for term in reversed(terms):  # need reverse since vbox has bottom-to-top direction
            if (text is None) or (text in term):
                object = QLabel(term)
                vbox.addWidget(object)

    def cancel_button(self) -> None:
        self.done(1)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        #print(f"key code: {event.key()}, text: {event.text()}")
        if event.key() == 16777216: # "ESC" pressed
            self.done(1)

    def ok_button(self) -> None:
        if self.add_data():
            self.done(0)

    def update_scroll_area_items(self, text: str) -> None:
        # See: https://stackoverflow.com/a/13103617/2173773
        layout = self.vbox
        for i in reversed(range(layout.count())):
            #layout.itemAt(i).widget().setParent(None)
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.add_scroll_area_items(self.vbox, text)
        #self.scrollwidget.setLayout(self.vbox)
        self.scrollwidget.update()


class Config():
    def __init__(self):
        self.dir = self.check_config_dir()
        self.fn = os.path.join(self.dir, 'config.ini')
        self.read_config()
        self.datefmt_str = '%Y-%m-%d %H:%M:%S'

    def get_dir(self) -> None:
        return self.dir

    def read_config(self) -> None:
        if not os.path.exists(self.fn):
            with open(self.fn, "w") as fp:
                pass
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
            }
        }
        config.read_dict(defaults)
        config.read(self.fn)
        self.config = config

    def check_config_dir(self) -> str:
        dir = ".vocabuilder"
        if not os.path.exists(dir):
            os.mkdir(dir)
        return dir


class CsvDatabaseHeader():
    status = "Status"
    term1 = "Term1"
    term2 = "Term2"
    test_delay = "TestDelay"
    last_test = "LastTest"
    header = [status, term1, term2, test_delay, last_test]


class CSVwrapper():
    def __init__(self, dbname: str):
        self.quotechar = '"'
        self.delimiter = ','
        self.filename = dbname
        self.header = CsvDatabaseHeader()

    def append_line(self, row_dict: dict):
        row = self.dict_to_row(row_dict)
        self.append_row(row)

    def append_row(self, row):
        with open(self.filename, "a", newline='') as fp:
            csvwriter = csv.writer(
                fp, delimiter=self.delimiter, quotechar=self.quotechar, quoting=csv.QUOTE_MINIMAL)
            csvwriter.writerow(row)

    def dict_to_row(self, row_dict: dict) -> None:
        row = []
        for key in self.header.header:
            row.append(row_dict[key])
        return row

    def open_for_write(self) -> "CSVwrapperWriter":
        return CSVwrapperWriter(self, self.filename)


class CSVwrapperWriter():
    """Context manager for writing lines to a csv file"""
    def __init__(self, parent: CSVwrapper, filename: str):
        self.parent = parent
        self.fp = open(filename, 'w', newline='')
        self.csvwriter = csv.writer(
            self.fp,
            delimiter=self.parent.delimiter,
            quotechar=self.parent.quotechar,
            quoting=csv.QUOTE_MINIMAL)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        self.fp.close()
        return False  # TODO: handle exceptions

    def writerow(self, row: list[str]) -> None:
        self.csvwriter.writerow(row)

    def writeline(self, row_dict: dict) -> None:
        self.csvwriter.writerow(self.parent.dict_to_row(row_dict))


class Database(DateMixin):
    def __init__(self, config: "Config"):
        self.config = config
        self.configdir = config.get_dir()
        self.db = {}
        self.status = TermStatus()
        self.header = CsvDatabaseHeader()
        self.dbname = os.path.join(self.configdir, "database.csv")
        self.csvwrapper = CSVwrapper(self.dbname)
        self.backupdir = os.path.join(self.configdir, "backup")
        self.maybe_create_db()
        self.maybe_create_backup_repo()
        self.read_database()
        self.create_backup()
        self.write_cleaned_up()

    def add_item(self, item: dict) -> None:
        item[self.header.status] = self.status.NOT_DELETED
        db_object = item.copy()
        term1 = db_object.pop(self.header.term1)
        self.db[term1] = db_object
        self.csvwrapper.append_line(item)
        logging.info(f"ADDED: term1 = '{term1}', "
                     f"term2 = '{item[self.header.term2]}', "
                     f"delay = '{item[self.header.test_delay]}', "
                     f"last_test = '{item[self.header.last_test]}'")

    def check_term1_exists(self, term1: str) -> bool:
        return term1 in self.db

    def create_backup(self) -> None:
        shutil.copy(self.dbname, self.backupdir)
        repo = git.Repo(self.backupdir)
        index = repo.index
        index.add([os.path.basename(self.dbname)])
        author = git.Actor("vocabuilder", "hakon.hagland@gmail.com")
        committer = author
        index.commit("Startup commit", author=author, committer=committer)
        logging.info(f"Created backup.")

    def delete_item(self, term1: str) -> None:
        item = self.db[term1].copy()
        item[self.header.status] = self.status.DELETED
        item[self.header.term1] = term1
        self.csvwrapper.append_line(item)
        logging.info(f"DELETED: term1 = '{term1}', term2 = '{item[self.header.term2]}'")
        del self.db[term1]

    def get_pairs_exceeding_test_delay(self) -> list[tuple[str,str]]:
        today = datetime.datetime.now()
        keys = self.get_term1_list()
        pairs = []
        for key in keys:
            values = self.db[key]
            last_test = values[self.header.last_test]
            candidate = False
            if last_test == "NA":
                candidate = True
            else:
                last_test = datetime.datetime.strptime(last_test, self.config.datefmt_str)
                diff = today - last_test
                days_since_last_test = diff.days
                test_delay = int(values[self.header.test_delay])
                if days_since_last_test >= test_delay:
                    candidate = True
            if candidate:
                term2 = values[self.header.term2]
                pairs.append((key, term2))
        return pairs

    def get_random_pair(self) -> tuple[str,str]:
        pairs = self.get_pairs_exceeding_test_delay()
        if len(pairs) == 0:
            return None
        max = len(pairs) - 1
        min = 0
        idx = random.randint(min, max)
        return pairs[idx]

    def get_term1_data(self, term1: str) -> str:
        return self.db[term1]

    def get_term1_list(self) -> list[str]:
        return sorted(self.db.keys())

    def get_term2(self, term1: str) -> str:
        return self.db[term1][self.header.term2]

    def maybe_create_backup_repo(self) -> None:
        if not os.path.exists(self.backupdir):
            os.mkdir(self.backupdir)
        gitdir = os.path.join(self.backupdir, '.git')
        if not os.path.exists(gitdir):
            git.Repo.init(self.backupdir)

    def maybe_create_db(self) -> None:
        # Status: 0 = The item has been deleted, 1, 2, 3,.. the item is not deleted
        # Term1     : "From" term
        # Term2     : "To" term (translation of Term1)
        # TestDelay : Number of days to next possible test, 0 or negative means no delay
        if not os.path.exists(self.dbname):
            self.csvwrapper.append_row(self.header.header)

    def read_database(self) -> None:
        filename = self.dbname
        with open(filename, "r") as fp:
            # TODO: This is the only place in the code where we are reading from db on file,
            # so we are lazy and don't delegate this to csvwrapper yet..
            delimiter = self.csvwrapper.delimiter
            quotechar = self.csvwrapper.quotechar
            csvh = csv.DictReader(fp, delimiter=delimiter, quotechar=quotechar)
            line = 1
            for row in csvh:
                if len(row) != len(self.header.header):
                    raise Exception(f'Currupt database, expected {len(self.header.header)} items,'
                                    f'got {len(row)} items')
                status = row[self.header.status]
                term1 = row[self.header.term1]
                if status == self.status.NOT_DELETED:
                    self.db[term1] = {
                        self.header.term2      : row[self.header.term2],
                        self.header.status     : status,
                        self.header.test_delay : row[self.header.test_delay],
                        self.header.last_test  : row[self.header.last_test]
                    }
                elif status == self.status.DELETED:
                    if term1 in self.db:
                        del self.db[term1]
                else:
                    raise DatabaseException(
                        f"Unexpected value for status at line {line} in file {filename}")
                line += 1
        logging.info(f"Read {len(self.db.keys())} lines from database")

    def update_dbfile_item(self, term1: str) -> None:
        """Write the data for db[term1] to the database file"""
        item = self.db[term1].copy()
        item[self.header.term1] = term1
        self.csvwrapper.append_line(item)
        logging.info( f"UPDATED: term1 = '{term1}', "
                      f"term2 = '{item[self.header.term2]}', "
                      f"delay = '{item[self.header.test_delay]}', "
                      f"last_test = '{item[self.header.last_test]}'")

    def update_item(self, term1: str, item: dict) -> None:
        self.db[term1] = item.copy()
        self.update_dbfile_item(term1)

    def update_retest_value(self, term1: str, delay: str) -> None:
        self.db[term1][self.header.test_delay] = delay
        today = self.today_as_string()
        self.db[term1][self.header.last_test] = today
        self.update_dbfile_item(term1)

    def write_cleaned_up(self) -> None:
        terms = self.get_term1_list()
        with self.csvwrapper.open_for_write() as fp:
            fp.writerow(self.header.header)
            for term1 in terms:
                item = self.db[term1].copy()
                item[self.header.term1] = term1
                fp.writeline(item)
        logging.info(f"Wrote cleaned up version of DB")


class MainWindow(QMainWindow):
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
        names = ['Add', 'Modify', 'Test', 'Delete', 'View', 'Backup']
        positions = [(0,0), (0,1), (0,2), (1,0), (1,1), (1, 2) ]
        callbacks = [self.add_new_entry, self.modify_entry, self.run_test,
                     self.delete_entry, self.view_entries, self.backup]

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
        print("Delete entry. Not implemented yet")

    def keyPressEvent(self, event: QKeyEvent) -> None:
        #print(f"key code: {event.key()}, text: {event.text()}")
        keys = [65, 66, 68, 77, 84, 86, 16777216]  # a, b, d, m, r, v, esc
        callbacks = [self.add_new_entry, self.backup, self.delete_entry, self.modify_entry, self.run_test,
                      self.view_entries, self.quit]
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
        print("View entries. Not implemented yet")


class ModifyWindow1(QDialog, WarningsMixin, DateMixin, StringMixin):
    """Modify/edit the translation of an existing term1 (and/or its translation) and update the
    database. Then, ask for a another term to add. Continue the above
    procedure of modifying terms until the user clicks the cancel button"""
    def __init__(self, parent: "MainWindow"):
        super().__init__(parent)  # make dialog modal
        self.parent = parent
        self.config = parent.config
        self.header = CsvDatabaseHeader()
        self.button_config = self.config.config["Buttons"]
        self.window_config = self.config.config["ModifyWindow1"]
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
        self.setWindowTitle("Choose item to modify")
        layout = QGridLayout()
        vpos = 0
        self.add_scroll_area(layout, vpos)
        vpos += 1
        vpos = self.add_line_edit(layout, vpos)
        self.add_buttons(layout, vpos)
        self.setLayout(layout)
        #widget = QWidget()
        ##widget.setLayout(layout)
        #self.setCentralWidget(widget)
        self.exec()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> None:
        self.buttons = []
        names = ['&Ok', '&Cancel']
        positions = [(vpos, 0), (vpos, 2) ]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(names):
            button = QPushButton(name, self)
            self.buttons.append(button)
            button.setMinimumWidth(int(self.button_config["MinWidth"]))
            button.setMinimumHeight(int(self.button_config["MinHeight"]))
            button.clicked.connect(callbacks[i])
            layout.addWidget(button, *positions[i], 1, 2)
        return vpos + 1

    def add_line_edit(self, layout: QGridLayout, vpos: int):
        large = self.config.config["FontSize"]["Large"]
        self.edits = {}
        descriptions = ['Term1:']
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
        self.scroll = QScrollArea()
        self.scrollwidget = QWidget()
        self.vbox = QVBoxLayout()
        self.vbox.addStretch()  # https://stackoverflow.com/a/63438161/2173773
        self.vbox.setDirection(QBoxLayout.Direction.BottomToTop)
        self.add_scroll_area_items(self.vbox)
        self.scrollwidget.setLayout(self.vbox)
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setWidgetResizable(True)
        self.scroll.setWidget(self.scrollwidget)
        layout.addWidget(self.scroll, vpos, 0, 1, 4)
        return

    def add_scroll_area_items(self, vbox: QVBoxLayout, text=None) -> None:
        terms = self.parent.db.get_term1_list()
        for term in reversed(terms):  # need reverse since vbox has bottom-to-top direction
            if (text is None) or (text in term):
                label = QLabelClickable(term)
                label.addCallback(self.scroll_area_item_clicked(term))
                vbox.addWidget(label)

    def cancel_button(self) -> None:
        self.done(1)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        #print(f"key code: {event.key()}, text: {event.text()}")
        if event.key() == 16777216: # "ESC" pressed
            self.done(1)

    def modify_item(self) -> None:
        term1 = self.edits[self.header.term1].text()
        if self.check_space_or_empty_str(term1):
            self.display_warning(self, 'Term1 is empty')
            return False
        if not self.parent.db.check_term1_exists(term1):
            self.display_warning(self, 'Term1 does not exist in database')
            return False
        ModifyWindow2(self, term1, self.parent.db)

    def ok_button(self) -> None:
        self.modify_item()

    def scroll_area_item_clicked(self, item: str) -> Callable[[], None]:
        def callback():
            self.edits[self.header.term1].setText(item)
        return callback

    def update_scroll_area_items(self, text: str) -> None:
        # See: https://stackoverflow.com/a/13103617/2173773
        layout = self.vbox
        for i in reversed(range(layout.count())):
            #layout.itemAt(i).widget().setParent(None)
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.add_scroll_area_items(self.vbox, text)
        #self.scrollwidget.setLayout(self.vbox)
        self.scrollwidget.update()

class ModifyWindow2(QDialog, WarningsMixin, DateMixin, StringMixin):
    """Modify/edit the translation of an existing term1 (and/or its translation) and update the
    database."""
    def __init__(self, parent: QDialog, term1: str, database: Database):
        super().__init__(parent)  # make dialog modal
        self.parent = parent
        self.term1 = term1
        self.db = database
        self.header = CsvDatabaseHeader()
        self.term2 = self.db.get_term2(self.term1)
        self.config = parent.config
        self.button_config = self.config.config["Buttons"]
        self.window_config = self.config.config["ModifyWindow2"]
        self.resize(int(self.window_config["Width"]), -1)
        #self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
        self.setWindowTitle("Modify item")
        layout = QGridLayout()
        vpos = 0
        vpos = self.add_labels(layout, vpos)
        vpos = self.add_line_edits(layout, vpos)
        self.add_buttons(layout, vpos)
        self.setLayout(layout)
        self.exec()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> None:
        self.buttons = []
        names = ['&Ok', '&Cancel']
        positions = [(vpos, 0), (vpos, 2) ]
        callbacks = [self.ok_button, self.cancel_button]

        for i, name in enumerate(names):
            button = QPushButton(name, self)
            self.buttons.append(button)
            button.setMinimumWidth(int(self.button_config["MinWidth"]))
            button.setMinimumHeight(int(self.button_config["MinHeight"]))
            button.clicked.connect(callbacks[i])
            layout.addWidget(button, *positions[i], 1, 2)
        return vpos + 1

    def add_labels(self, layout: QGridLayout, vpos: int) -> None:
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

    def add_line_edits(self, layout: QGridLayout, vpos: int):
        large = self.config.config["FontSize"]["Large"]
        self.edits = {}
        descriptions = ['New term1:', 'New term2:']
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
        #print(f"key code: {event.key()}, text: {event.text()}")
        if event.key() == 16777216: # "ESC" pressed
            self.done(1)

    def modify_item(self) -> bool:
        old_term1 = self.term1
        new_term1 = self.edits[self.header.term1].text()
        new_term2 = self.edits[self.header.term2].text()
        if self.check_space_or_empty_str(new_term1):
            self.display_warning(self, 'Term1 is empty')
            return False
        if self.check_space_or_empty_str(new_term2):
            self.display_warning(self, 'Term2 is empty')
            return False
        item = self.db.get_item(old_term1).copy()
        if new_term1 == old_term1:
            item[self.header.term2] = new_term2
            self.db.update_item(item)
        else:
            item[self.header.term1] = new_term1
            item[self.header.term2] = new_term2
            self.db.delete_item(old_term1)
            self.db.add_item(item)
        return True

    def ok_button(self) -> None:
        if self.modify_item():
            self.done(0)

    def scroll_area_item_clicked(self, item: str) -> Callable[[], None]:
        def callback():
            self.edits[self.header.term1].setText(item)
        return callback

    def update_scroll_area_items(self, text: str) -> None:
        # See: https://stackoverflow.com/a/13103617/2173773
        layout = self.vbox
        for i in reversed(range(layout.count())):
            #layout.itemAt(i).widget().setParent(None)
            widget = layout.itemAt(i).widget()
            if widget is not None:
                widget.deleteLater()
        self.add_scroll_area_items(self.vbox, text)
        #self.scrollwidget.setLayout(self.vbox)
        self.scrollwidget.update()


class QLabelClickable(QLabel):
    def __init__(self, text: str, parent: QWidget = None):
        super().__init__(text, parent)
        self.clicked_callback = None

    def addCallback(self, callback: Callable[[], None]):
        self.clicked_callback = callback

    def mousePressEvent(self, ev: QMouseEvent) -> None:
        if self.clicked_callback is not None:
            self.clicked_callback()
        return super().mousePressEvent(ev)


class TermStatus():
    """Has this term been deleted from the database?"""
    DELETED = "0"
    NOT_DELETED = "1"


class TestDirection():
    """When running a practice/test session, should you practice translating words from language 1 to
    language 2, or practice translating words from language 2 to language 1?
    """
    _1to2 = 1
    _2to1 = 2


class TestMethod():
    """When running a practice/test session, should the words to be practiced be picked at random,
    or should the user select the words from a list?"""
    Random = 1
    List = 2


class TestWindow(QDialog, WarningsMixin):
    def __init__(self, parent: MainWindow):
        super().__init__(parent)  # make dialog modal
        self.parent = parent
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
        pair = self.parent.db.get_random_pair()
        if pair is None:
            self.display_warning(self, 'No terms ready for practice today!')
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

    def add_current_term_to_practice(self, layout: QGridLayout, vpos: int, term1: str) -> None:
        fontsize = self.config.config["FontSize"]["Large"]
        groupbox = QGroupBox("Word/term/phrase to practice")
        grid = QGridLayout()
        label11 = QLabel(f"Translate this term:")
        grid.addWidget(label11, 0, 0)
        label12 = QLabel(f"{term1}")
        self.term1_label = label12
        term1_color = self.config.config["FontColor"]["Blue"]
        label12.setStyleSheet(f"QLabel {{font-size: {fontsize}; color: {term1_color}; }}")
        grid.addWidget(label12, 0, 1)
        label21 = QLabel(f"Type translation here:")
        grid.addWidget(label21, 1, 0)
        edit = QLineEdit(self)
        edit.setStyleSheet(f"QLineEdit {{font-size: {fontsize};}}")
        self.user_edit = edit
        grid.addWidget(edit, 1, 1)
        button = QPushButton("&Show translation: ", self)
        grid.addWidget(button, 2, 0)
        label32 = QLabel(self.config.config["Practice"]["HiddenText"])
        self.hidden_label = label32
        term2_color = self.config.config["FontColor"]["Red"]
        label32.setStyleSheet(f"QLabel {{font-size: {fontsize}; color: {term2_color}; }}")
        grid.addWidget(label32, 2, 1)
        button.clicked.connect(self.show_hidden_translation(label32))
        groupbox.setLayout(grid)
        layout.addWidget(groupbox, vpos, 0, 1, 2)
        vpos += 1
        return vpos

    def add_next_done_buttons(self, layout: QGridLayout, vpos: int):
        next_button = QPushButton("&Next", self)
        next_button.clicked.connect(self.next_button_clicked)
        layout.addWidget(next_button, vpos, 0)
        done_button = QPushButton("&Done", self)
        done_button.clicked.connect(self.done_button_clicked)
        layout.addWidget(done_button, vpos, 1)
        return vpos + 1

    def add_param_info_labels(self, layout: QGridLayout, vpos: int):
        if self.params.test_direction == TestDirection._1to2:
            lang1 = 1
            lang2 = 2
        else:
            lang1 = 2
            lang2 = 1
        groupbox = QGroupBox("Parameters")
        grid = QGridLayout()
        label11 = QLabel(f"<i>Direction:</i>")
        label11.setStyleSheet("QLabel {color: #ffb84d}")
        grid.addWidget(label11, 0, 0)
        label12 = QLabel(f"{lang1} -> {lang2}")
        grid.addWidget(label12, 0, 1)
        if self.params.test_method == TestMethod.Random:
            ttype = "Random"
        else:
            ttype = "Choose"
        label21 = QLabel(f"<i>Choose type:</i>")
        label21.setStyleSheet("QLabel {color: #ffb84d}")
        grid.addWidget(label21, 1, 0)
        label22 = QLabel(f"{ttype}")
        grid.addWidget(label22, 1, 1)
        groupbox.setLayout(grid)
        layout.addWidget(groupbox, vpos, 0, 1, 2)
        return vpos + 1

    def add_retest_options(self, layout: QGridLayout, vpos: int):
        groupbox = QGroupBox("When to practice this word again?")
        grid = QGridLayout()
        label11 = QLabel(f"<i>Practice this word again after x days:</i>")
        label11.setStyleSheet("QLabel {color: #ffb84d}")
        grid.addWidget(label11, 0, 0, 1, 2)
        edit = QLineEdit(self)
        self.delay_edit = edit
        edit.setText("1")
        validator = QIntValidator()
        validator.setBottom(0)
        edit.setValidator(validator)
        #edit.setStyleSheet(f"QLineEdit {{font-size: {fontsize};}}")
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
            self, grid: QGridLayout, i: int, delay: int, checked: bool, edit: QLineEdit) -> None:
        day_str = "days"
        if delay == 1:
            day_str = "day"
        radio = QRadioButton(f"{delay} {day_str}")
        radio.setChecked(checked)
        radio.clicked.connect(self.update_retest_lineedit(edit, str(delay)))
        vpos = i // 3
        hpos = i % 3
        grid.addWidget(radio, vpos+1, hpos)

    def done_button_clicked(self) -> None:
        delay = self.delay_edit.text()
        self.parent.db.update_retest_value(self.term1, delay)
        self.done(0)

    def keyPressEvent(self, event: QKeyEvent) -> None:
        #print(f"key code: {event.key()}, text: {event.text()}")
        if event.key() == 16777216: # "ESC" pressed
            self.done(1)

    def next_button_clicked(self) -> None:
        delay = self.delay_edit.text()
        self.parent.db.update_retest_value(self.term1, delay)
        pair = self.parent.db.get_random_pair()
        if pair is None:
            self.display_warning(self, 'No more terms ready for practice today!')
            self.done(1)
        term1, term2 = pair
        self.term1 = term1
        self.term2 = term2
        self.term1_label.setText(term1)
        self.hidden_label.setText(self.config.config["Practice"]["HiddenText"])
        self.user_edit.setText("")
        self.user_edit.setFocus()


    def show_hidden_translation(self, label: QLabel) -> Callable[[], None]:
        def callback():
            label.setText(self.term2)
        return callback

    def update_retest_lineedit(self, edit: QLineEdit, delay: str) -> Callable[[], None]:
        def callback():
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
        #vpos = self.add_line_edits(layout, vpos)
        vpos = self.add_buttons(layout, vpos)
        self.setLayout(layout)
        self.exec()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        names = ['Ok', 'Cancel']
        positions = [(vpos, 0), (vpos, 1) ]
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
        #vbox.addStretch(1)
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
        #vbox.addStretch(1)
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
#--------------------
def main():
    config = Config()
    db = Database(config)
    app = QApplication(sys.argv)
    window = MainWindow(app, db, config)
    window.show()
    app.exec()

if __name__ == "__main__":
    main()


