from __future__ import annotations

# import logging
import typing

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QCloseEvent, QIntValidator, QKeyEvent
from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QToolTip,
    QWidget,
)

from vocabuilder.config import Config
from vocabuilder.csv_helpers import CsvDatabaseHeader
from vocabuilder.database import Database
from vocabuilder.mixins import ResizeWindowMixin, StringMixin, TimeMixin, WarningsMixin
from vocabuilder.type_aliases import DatabaseRow
from vocabuilder.widgets import QSelectItemScrollArea


class AddWindow(QWidget, ResizeWindowMixin, StringMixin, TimeMixin, WarningsMixin):
    """Add a new term (and its translation) to the database, then ask for a another term to add.
    Continue the above procedure of adding terms until the user clicks the cancel button
    """

    def __init__(self, parent: QWidget, config: Config, database: Database):
        super().__init__()
        # NOTE: using "parent_" to avoid confilict with "parent" method in QWidget
        self.parent_ = parent
        self.config = config
        self.db = database
        self.header = CsvDatabaseHeader()
        self.window_config = typing.cast(
            dict[str, str], self.config.config["AddWindow"]
        )
        self.button_config = self.config.config["Buttons"]
        self.resize_window_from_config()
        self.setWindowTitle("Add new item")
        layout = QGridLayout()
        vpos = 0
        self.add_scroll_area(layout, vpos)
        vpos += 1
        self.edits: dict[str, QLineEdit] = {}  # mypy requires type annotation here
        vpos = self.add_line_edits(layout, vpos)
        self.add_buttons(layout, vpos)
        self.setLayout(layout)
        self.show()

    def add_buttons(self, layout: QGridLayout, vpos: int) -> int:
        """Adds the button widgets.
        :param layout:
        """
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
            button.clicked.connect(callbacks[i])  # type: ignore[unused-ignore, arg-type]
            layout.addWidget(button, *positions[i])
        return vpos + 1

    def add_button_pressed(self) -> bool:
        if self.add_data():
            self.edits[self.header.term1].setText("")
            self.edits[self.header.term2].setText("")
            self.edits[self.header.test_delay].setText("")
            self.edits[self.header.term1].setFocus()
            return True
        return False

    def add_data(self) -> bool:
        term1 = self.edits[self.header.term1].text()
        if self.check_space_or_empty_str(term1):
            self.display_warning(self, "Term1 is empty")
            return False
        if self.db.check_term1_exists(term1):
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
        self.db.add_item(item)
        items = self.get_db().get_term1_list()
        # NOTE: update view window later when reaching the QT eventloop
        self.maybe_update_view_window_later()
        self.scrollarea.update_items_list(items)
        return True

    def add_line_edits(self, layout: QGridLayout, vpos: int) -> int:
        large = self.config.config["FontSize"]["Large"]
        descriptions = ["Term1:", "Term2:", "Retest in x days:"]
        fontsizes = [large, large, None]
        names = [self.header.term1, self.header.term2, self.header.test_delay]
        callbacks1 = [self.update_scroll_area_items, None, None]
        callbacks2 = [None, self.simulate_add_button_pressed, None]
        for i, desc in enumerate(descriptions):
            label = QLabel(desc)
            layout.addWidget(label, vpos, 0)
            edit = QLineEdit(self)
            if fontsizes[i] is not None:
                edit.setStyleSheet(f"QLineEdit {{font-size: {fontsizes[i]};}}")
            if callbacks1[i] is not None:
                edit.textChanged.connect(callbacks1[i])  # type: ignore
            if callbacks2[i] is not None:
                edit.returnPressed.connect(callbacks2[i])  # type: ignore
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
        self.close()

    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Overrides the closeEvent() method in QWidget. We use this to notify the
        parent when we are closed"""
        if event is not None:
            event.accept()
            self.parent_.add_window_closed()  # type: ignore

    def get_db(self) -> Database:
        return self.db

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        if (event is not None) and event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
            self.close()

    def maybe_update_view_window_later(self) -> None:
        if self.parent_.view_window_is_open():  # type: ignore

            def on_start() -> None:
                self.parent_.update_view_window()  # type: ignore

            QTimer.singleShot(0, on_start)

    def ok_button(self) -> None:
        if self.add_data():
            self.close()

    def simulate_add_button_pressed(self) -> None:
        term1 = self.edits[self.header.term1].text()
        if self.add_button_pressed():
            edit2 = self.edits[self.header.term2]
            point = edit2.pos()
            point = self.mapToGlobal(edit2.pos())
            QToolTip.showText(
                point, f"""Added: <font color="red">{term1}</font>""", msecShowTime=1400
            )

    def update_scroll_area_items(self, text: str) -> None:
        self.scrollarea.update_items(text)
