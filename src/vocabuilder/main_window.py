import logging
import platform
import subprocess
import typing
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QCloseEvent, QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QMainWindow,
    QMenu,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QWidget,
)

from vocabuilder.add_window import AddWindow
from vocabuilder.config import Config
from vocabuilder.database import Database
from vocabuilder.exceptions import ConfigException
from vocabuilder.mixins import WarningsMixin
from vocabuilder.modify_window import ModifyWindow
from vocabuilder.test_window import TestWindow
from vocabuilder.view_window import ViewWindow
from vocabuilder.widgets import QGridMinimalLabel, SelectWordFromList


class MainWindow(QMainWindow, WarningsMixin):
    def __init__(self, app: QApplication, db: Database, config: "Config"):
        super().__init__()
        self.config = config
        self.button_config = self.config.config["Buttons"]
        self.window_config = self.config.config["MainWindow"]
        # NOTE: Seems like mypy is reading from top to bottom, so these types need to be
        # declared before they are used
        self.view_window: ViewWindow | None = None
        self.add_window: AddWindow | None = None
        self.test_window: TestWindow | None = None
        self.app = app
        self.db = db
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
        self.setWindowTitle("VocaBuilder")
        self.create_menus()
        layout = QGridLayout()
        layout.setContentsMargins(
            int(self.window_config["MarginLeft"]),
            int(self.window_config["MarginTop"]),
            int(self.window_config["MarginRight"]),
            int(self.window_config["MarginBottom"]),
        )
        vpos = 0
        vpos = self.add_database_info_label(layout, vpos)
        self.add_buttons(layout, vpos)
        widget = QWidget()
        widget.setLayout(layout)
        self.setCentralWidget(widget)

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        self.buttons = []
        names = ["Add", "Modify", "Test", "Delete", "View", "Backup"]
        # NOTE: this dict is used only for testing purposes
        self.button_names = {names[i]: i for i in range(len(names))}
        positions = [
            (vpos, 0),
            (vpos, 1),
            (vpos, 2),
            (vpos + 1, 0),
            (vpos + 1, 1),
            (vpos + 1, 2),
        ]
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
        return vpos + 2

    def add_database_info_label(self, layout: QGridLayout, vpos: int) -> int:
        name = self.db.get_voca_name()
        color = self.config.config["FontColor"]["Red"]
        label = QGridMinimalLabel(
            f"Vocabulary: <span style='color: {color};'>{name}</span>"
        )
        label.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Maximum)
        layout.addWidget(label, vpos, 0, 1, 3)
        layout.setRowStretch(vpos, 0)
        return vpos + 1

    def add_new_entry(self) -> None:
        if self.add_window is None:
            self.add_window = AddWindow(self, self.config, self.db)
        else:
            self.add_window.activateWindow()

    def add_window_closed(self) -> None:
        self.add_window = None
        logging.info("AddWindow closed")

    def backup(self) -> None:
        self.db.create_backup()

    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Overrides the closeEvent() method in QWidget to ensure that all windows
        are closed when the main window is closed"""
        if event is not None:
            event.accept()
            self.quit()

    def create_file_menu(self) -> None:
        file_menu = QMenu("&File", self)
        self.menu_bar.addMenu(file_menu)
        self.edit_config_action = QAction("&Edit config file", self)
        file_menu.addAction(self.edit_config_action)
        self.edit_config_action.setShortcut("Ctrl+E")
        self.edit_config_action.triggered.connect(self.edit_config)

    def create_database_menu(self) -> None:
        database_menu = QMenu("&Database", self)
        self.menu_bar.addMenu(database_menu)
        self.reset_fb_action = QAction(
            "Reset firebase database from local database", self
        )
        database_menu.addAction(self.reset_fb_action)
        self.reset_fb_action.triggered.connect(self.reset_firebase)

    def create_menus(self) -> None:
        self.menu_bar = QMenuBar(self)
        self.setMenuBar(self.menu_bar)
        self.create_file_menu()
        self.create_database_menu()
        # self.create_edit_menu()
        # self.create_help_menu()

    def delete_entry(self) -> QMessageBox:
        mbox = self.display_warning(self, "Delete entry. Not implemented yet")
        return mbox

    def edit_config(self) -> None:
        cfg = self.config.config["Editor"]
        config_path = str(self.config.get_config_path())
        if platform.system() == "Linux":
            editor = cfg["Linux"]
            cmd = editor
            args = [config_path]
        elif platform.system() == "Darwin":
            cmd = "open"
            editor = cfg["MacOS"]
            args = ["-a", editor, config_path]
        elif platform.system() == "Windows":
            editor = cfg["Windows"]
            cmd = editor
            args = [config_path]
        else:
            raise ConfigException(f"Unknown platform: {platform.system()}")
        subprocess.Popen([cmd, *args], start_new_session=True)

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        keys = [
            Qt.Key.Key_A,
            Qt.Key.Key_B,
            Qt.Key.Key_D,
            Qt.Key.Key_M,
            Qt.Key.Key_Q,
            Qt.Key.Key_R,
            Qt.Key.Key_V,
            Qt.Key.Key_Escape,
        ]  # a, b, d, m, r, v, esc
        callbacks = [
            self.add_new_entry,
            self.backup,
            self.delete_entry,
            self.modify_entry,
            self.quit,
            self.run_test,
            self.view_entries,
            self.quit,
        ]
        for i, key in enumerate(keys):
            if (event is not None) and event.key() == key:
                callbacks[i]()

    def modify_entry(self) -> SelectWordFromList:
        """Modify/edit the translation of an existing term1 (and/or its translation)
        and update the database. Then, ask for a another term to modify. Continue
        the above procedure of modifying terms until the user clicks the cancel
        button"""

        def callback(pair: tuple[str, str]) -> None:
            word = pair[0]
            ModifyWindow(self, word, self.config, self.db)

        win_title = "Choose item to modify"
        self.items = self.db.get_term1_list()

        def get_pair_callback(word: str, idx: int) -> tuple[str, str]:
            return word, self.db.get_term2(word)

        options = {"click_accept": True}
        dialog = SelectWordFromList(
            self,
            self.config,
            win_title,
            self.items,
            callback,
            get_pair_callback,
            options,
        )
        return dialog

    def quit(self) -> None:
        logging.info("Quitting the application")
        self.app.quit()

    def reset_firebase(self) -> None:
        self.db.reset_firebase()

    def run_test(self) -> None:
        if self.test_window is None:
            self.test_window = TestWindow(self, self.config, self.db)
        else:
            self.test_window.activateWindow()

    def test_window_closed(self) -> None:
        self.test_window = None
        logging.info("TestWindow closed")

    def update_view_window(self) -> None:
        if self.view_window is not None:
            self.view_window.update_from_database()

    def view_entries(self) -> None:
        if self.view_window is None:
            self.view_window = ViewWindow(self, self.config, self.db)
        else:
            self.view_window.activateWindow()

    def view_window_closed(self) -> None:
        self.view_window = None
        logging.info("ViewWindow closed")

    def view_window_is_open(self) -> bool:
        return self.view_window is not None
