from __future__ import annotations

import logging
from typing import Callable
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import (
    QGridLayout,
    QLineEdit,
    QScrollArea,
    QWidget,
)
from vocabuilder.config import Config
from vocabuilder.database import Database
from vocabuilder.mixins import WarningsMixin
from vocabuilder.widgets import QLabelClickable


class ViewScrollArea(QScrollArea):
    def __init__(
        self,
        items1: list[str],
        items2: list[str],
        callback1: Callable[[str], None],
        callback2: Callable[[str], None],
    ):
        super().__init__()
        self.items1 = items1
        self.items2 = items2
        self.callback1 = callback1
        self.callback2 = callback2
        self.scrollwidget = QWidget()
        self.layout_ = (
            QGridLayout()
        )  # use layout_ to avoid name clash with QWidget.layout()
        self.add_items()
        self.scrollwidget.setLayout(self.layout_)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOn)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setWidgetResizable(True)
        self.setWidget(self.scrollwidget)
        return

    def add_items(self) -> None:
        vpos = 0
        for i in range(len(self.items1)):
            term1 = self.items1[i]
            term2 = self.items2[i]
            label1 = QLabelClickable(term1)
            label1.setStyleSheet("border: 1px solid #bbbbbb;")
            callback1 = self.item1_clicked(term1)
            label1.addCallback(callback1)
            self.layout_.addWidget(label1, vpos, 0)
            label2 = QLabelClickable(term2)
            label2.setStyleSheet("border: 1px solid #bbbbbb;")
            callback2 = self.item2_clicked(term2)
            label2.addCallback(callback2)
            self.layout_.addWidget(label2, vpos, 1)
            vpos += 1

    def item1_clicked(self, item1: str) -> Callable[[], None]:
        def callback() -> None:
            self.callback1(item1)

        return callback

    def item2_clicked(self, item2: str) -> Callable[[], None]:
        def callback() -> None:
            self.callback2(item2)

        return callback


class ViewWindow(QWidget, WarningsMixin):
    def __init__(self, parent: QWidget, config: Config, database: Database) -> None:
        super().__init__()
        self.parent_ = parent  # use parent_ to avoid name clash with QWidget.parent()
        self.db = database
        self.config = config
        self.window_config = self.config.config["ViewWindow"]
        self.setWindowTitle("View Database")
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
        layout = QGridLayout()
        vpos = 1
        vpos = self.add_line_edits(layout, vpos)
        vpos = self.add_scroll_area(layout, vpos)
        self.setLayout(layout)
        self.show()

    def add_line_edits(self, layout: QGridLayout, vpos: int) -> int:
        # large = self.config.config["FontSize"]["Large"]
        self.edit1 = QLineEdit(self)
        # edit1.textChanged.connect(update_scroll_area_items1)
        layout.addWidget(self.edit1, vpos, 0)
        self.edit2 = QLineEdit(self)
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

        self.scrollarea1 = ViewScrollArea(items1, items2, callback1, callback2)
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
