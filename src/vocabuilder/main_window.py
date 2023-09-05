import typing
from typing import Callable
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QApplication,
    QGridLayout,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QWidget,
)
from vocabuilder.add_window import AddWindow
from vocabuilder.config import Config
from vocabuilder.database import Database
from vocabuilder.widgets import QGridMinimalLabel, SelectWordFromList
from vocabuilder.modify_window import ModifyWindow
from vocabuilder.test_window import TestWindow
from vocabuilder.mixins import WarningsMixin


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

    def add_new_entry(self) -> AddWindow:
        return AddWindow(self, self.config, self.db)

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
        self.app.quit()

    def run_test(self) -> TestWindow:
        return TestWindow(self, self.config, self.db)

    def view_entries(self) -> QMessageBox:
        mbox = self.display_warning(self, "View entries. Not implemented yet")
        return mbox
