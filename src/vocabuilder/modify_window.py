from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QWidget,
)

from vocabuilder.config import Config
from vocabuilder.csv_helpers import CsvDatabaseHeader
from vocabuilder.database import Database
from vocabuilder.mixins import StringMixin, WarningsMixin


class ModifyWindow(QDialog, WarningsMixin, StringMixin):
    """Modify/edit the translation of an existing term1 (and/or its translation) and update the
    database.
    """

    def __init__(self, parent: QWidget, term1: str, config: Config, database: Database):
        super().__init__(parent)  # make dialog modal
        self.term1 = term1
        self.db = database
        self.header = CsvDatabaseHeader()
        self.term2 = self.db.get_term2(self.term1)
        self.config = config
        self.button_config = self.config.config["Buttons"]
        self.window_config = self.config.config["ModifyWindow"]
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
