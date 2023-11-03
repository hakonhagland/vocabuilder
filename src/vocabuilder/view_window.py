from __future__ import annotations

import logging
from typing import Callable, Optional
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QBoxLayout,
    QHBoxLayout,
    QGridLayout,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from vocabuilder.config import Config
from vocabuilder.database import Database
from vocabuilder.mixins import WarningsMixin
from vocabuilder.widgets import QLabelClickable


class MatchTerm:
    TERM1: int = 1
    TERM2: int = 2


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
        self.fontsize = fontsize
        self.vbox = QVBoxLayout()
        self.scrollwidget = QWidget()
        self.scrollwidget.setLayout(self.vbox)
        self.add_left_and_right_column()
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.scrollwidget)
        return

    def add_left_and_right_column(self) -> None:
        self.vbox.addStretch()  # https://stackoverflow.com/a/63438161/2173773
        self.vbox.setDirection(QBoxLayout.Direction.BottomToTop)
        self.vbox.setSpacing(0)
        self.vbox.setContentsMargins(0, 0, 0, 0)
        self.add_items()

    def add_items(
        self, text: Optional[str] = None, match_term: Optional[int] = None
    ) -> None:
        style = f"border: 1px solid #bbbbbb; font-size: {self.fontsize}"
        for i in reversed(range(len(self.items[0]))):
            if (match_term is not None) and (text is not None):
                if match_term == MatchTerm.TERM1:
                    term1 = self.items[0][i]
                    if not (text in term1):
                        continue
                elif match_term == MatchTerm.TERM2:
                    term2 = self.items[1][i]
                    if not (text in term2):
                        continue
            widget = QWidget()
            hbox = QHBoxLayout()
            hbox.setContentsMargins(0, 0, 0, 0)
            widget.setLayout(hbox)
            for j in range(0, 2):
                term = self.items[j][i]
                label = QLabelClickable(term)
                label.setStyleSheet(style)

                def callback(j: int = j, term: str = term) -> None:
                    self.callbacks[j](term)

                label.addCallback(callback)
                hbox.addWidget(label)
            self.vbox.addWidget(widget)

    def update_items1(self, text: str) -> None:
        self.update_items(text, MatchTerm.TERM1)

    def update_items2(self, text: str) -> None:
        self.update_items(text, MatchTerm.TERM2)

    def update_items(self, text: str, match_term: int) -> None:
        layout = self.vbox
        for i in reversed(range(layout.count())):
            layout_item = layout.itemAt(i)
            if layout_item is not None:
                widget = layout_item.widget()
                if widget is not None:
                    widget.deleteLater()
        self.add_items(text, match_term)
        self.scrollwidget.update()


class ViewWindow(QWidget, WarningsMixin):
    def __init__(self, parent: QWidget, config: Config, database: Database) -> None:
        super().__init__()
        self.parent_ = parent  # use parent_ to avoid name clash with QWidget.parent()
        self.db = database
        self.config = config
        self.window_config = self.config.config["ViewWindow"]
        self.fontsize = self.window_config["FontSize"]
        self.setWindowTitle("View Database")
        layout = QGridLayout()
        vpos = 1
        vpos = self.add_line_edits(layout, vpos)
        vpos = self.add_scroll_area(layout, vpos)
        self.setLayout(layout)
        if ("X" in self.window_config) and ("Y" in self.window_config):
            self.move(
                int(self.window_config["X"]),
                int(self.window_config["Y"]),
            )
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
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

    def get_db(self) -> Database:
        return self.db

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if (event is not None) and event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
            logging.info("ViewWindow: ESC pressed")
            self.close()

    def update_items1(self) -> None:
        self.scrollarea1.update_items1(self.edit1.text())

    def update_items2(self) -> None:
        self.scrollarea1.update_items2(self.edit2.text())
