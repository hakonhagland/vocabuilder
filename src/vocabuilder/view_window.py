from __future__ import annotations

import enum
import logging
import typing
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCloseEvent, QKeyEvent
from PyQt6.QtWidgets import (
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from vocabuilder.config import Config
from vocabuilder.database import Database
from vocabuilder.mixins import ResizeWindowMixin, WarningsMixin
from vocabuilder.widgets import QLabelClickable


class MatchTerm(enum.Enum):
    """Filter results based on the term1 or the term2 LineEdits"""

    TERM1 = "term1"
    TERM2 = "term2"


class ViewScrollArea(QScrollArea):
    def __init__(
        self,
        items1: list[str],
        items2: list[str],
        callback1: Callable[[str], None],
        callback2: Callable[[str], None],
        fontsize: str,
    ):
        super().__init__()
        self.items = [items1, items2]
        self.callbacks = [callback1, callback2]
        # We implement lazy loading of the items in the scroll area to avoid
        # performance issues when there are a large number of items.
        num_items = len(self.items[0])
        self.filtered_indices = list(
            range(num_items)  # Initially no filtering, so all items are included
        )
        self.loaded_rows = (
            0  # Will be updated below, and also in maybe_load_more_items()
        )
        self.add_increment = 40  # Add this many items at a time
        self.fontsize = fontsize
        self.vbox = QVBoxLayout()
        self.scrollwidget = QWidget()
        self.scrollwidget.setLayout(self.vbox)
        self.add_left_and_right_column()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.scrollwidget)
        if scrollbar := self.verticalScrollBar():
            scrollbar.valueChanged.connect(self.maybe_load_more_items)
        return

    def add_left_and_right_column(self) -> None:
        self.vbox.addStretch()  # https://stackoverflow.com/a/63438161/2173773
        # self.vbox.setDirection(QBoxLayout.Direction.TopToBottom)
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.add_items()

    def add_items(self) -> None:
        """Add a maximum of items self.add_increment items to the scroll area. This lazy
        loading of items is done to avoid performance issues when there are a large number
        of items."""
        style = f"border: 1px solid #bbbbbb; font-size: {self.fontsize}"
        added_rows = 0
        if self.loaded_rows > 0:
            self.vbox.takeAt(self.vbox.count() - 1)  # Remove the stretch
        for i in range(self.add_increment):
            if self.loaded_rows + i >= len(self.filtered_indices):
                break
            idx = self.filtered_indices[self.loaded_rows + i]
            widget = QWidget()
            hbox = QHBoxLayout()
            hbox.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(hbox)
            for j in range(0, 2):
                term = self.items[j][idx]
                label = QLabelClickable(term)
                label.setStyleSheet(style)

                def callback(j: int = j, term: str = term) -> None:
                    self.callbacks[j](term)

                label.addCallback(callback)
                hbox.addWidget(label)
            self.vbox.addWidget(widget)
            added_rows += 1
        self.vbox.addStretch()
        self.loaded_rows += added_rows

    def filter_items(self, text: str, match_term: MatchTerm) -> None:
        """Filter the items based on the text and the match_term"""
        self.filtered_indices = []
        num_items = len(self.items[0])
        self.loaded_rows = 0
        for i in range(num_items):
            if match_term == MatchTerm.TERM1:
                if text in self.items[0][i]:
                    self.filtered_indices.append(i)
            elif match_term == MatchTerm.TERM2:
                if text in self.items[1][i]:
                    self.filtered_indices.append(i)

    def maybe_load_more_items(self) -> None:
        if scrollbar := self.verticalScrollBar():
            if scrollbar.value() == scrollbar.maximum():
                self.add_items()

    def update_items1(self, text: str) -> None:
        self.update_items(text, MatchTerm.TERM1)

    def update_items2(self, text: str) -> None:
        self.update_items(text, MatchTerm.TERM2)

    def update_items(self, text: str, match_term: MatchTerm) -> None:
        layout = self.vbox
        for i in reversed(range(layout.count())):
            layout_item = layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if widget is not None:
                    widget.deleteLater()
        self.filter_items(text, match_term)
        self.add_items()
        self.scrollwidget.update()

    def update_items_from_db(
        self, items1: list[str], items2: list[str], text1: str, text2: str
    ) -> None:
        self.items = [items1, items2]
        # logging.info(f"update_items_from_db: {text1}, {text2}")
        if len(text2) > 0:
            self.update_items2(text2)
        else:
            self.update_items1(text1)


class ViewWindow(QWidget, ResizeWindowMixin, WarningsMixin):
    def __init__(self, parent: QWidget, config: Config, database: Database) -> None:
        super().__init__()
        self.parent_ = parent  # use parent_ to avoid name clash with QWidget.parent()
        self.db = database
        self.config = config
        self.window_config = typing.cast(
            dict[str, str], self.config.config["ViewWindow"]
        )
        self.fontsize = self.window_config["FontSize"]
        self.setWindowTitle("View Database")
        layout = QGridLayout()
        vpos = 1
        vpos = self.add_line_edits(layout, vpos)
        vpos = self.add_scroll_area(layout, vpos)
        self.setLayout(layout)
        self.resize_window_from_config()
        # self.setGeometry()
        self.show()

    def add_line_edits(self, layout: QGridLayout, vpos: int) -> int:
        # large = self.config.config["FontSize"]["Large"]
        self.edit1 = QLineEdit(self)
        style = f"font-size: {self.fontsize}"
        self.edit1.setStyleSheet(style)
        self.edit1.textChanged.connect(self.update_items1)
        # edit1.textChanged.connect(update_scroll_area_items1)
        layout.addWidget(self.edit1, vpos, 0)
        self.edit2 = QLineEdit(self)
        self.edit2.setStyleSheet(style)
        self.edit2.textChanged.connect(self.update_items2)
        # edit2.textChanged.connect(update_scroll_area_items2)
        layout.addWidget(self.edit2, vpos, 1)
        vpos += 1
        return vpos

    def add_scroll_area(self, layout: QGridLayout, vpos: int) -> int:
        items1 = self.get_db().get_term1_list()
        items2 = self.get_db().get_term2_list()

        def callback1(text: str) -> None:
            self.edit1.setText(text)

        def callback2(text: str) -> None:
            self.edit2.setText(text)

        self.scrollarea1 = ViewScrollArea(
            items1, items2, callback1, callback2, self.fontsize
        )
        layout.addWidget(self.scrollarea1, vpos, 0, 1, 2)

        vpos += 1
        return vpos

    def closeEvent(self, event: QCloseEvent | None) -> None:
        """Overrides the closeEvent() method in QWidget. We use this to notify the
        parent when we are closed"""
        if event is not None:
            event.accept()
            # parent = typing.cast(MainWindow, self.parent_)
            self.parent_.view_window_closed()  # type: ignore

    def get_db(self) -> Database:
        return self.db

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if (event is not None) and event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
            logging.info("ViewWindow: ESC pressed")
            self.close()

    def update_from_database(self) -> None:
        items1 = self.get_db().get_term1_list()
        items2 = self.get_db().get_term2_list()
        self.scrollarea1.update_items_from_db(
            items1, items2, self.edit1.text(), self.edit2.text()
        )

    def update_items1(self, txt: str) -> None:
        self.scrollarea1.update_items1(txt)

    def update_items2(self, txt: str) -> None:
        self.scrollarea1.update_items2(txt)
