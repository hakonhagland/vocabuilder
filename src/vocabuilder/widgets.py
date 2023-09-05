# import logging
import typing
from typing import Any, Callable
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QKeyEvent, QMouseEvent
from PyQt6.QtWidgets import (
    QBoxLayout,
    QDialog,
    QGridLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)
from vocabuilder.config import Config
from vocabuilder.csv_helpers import CsvDatabaseHeader
from vocabuilder.mixins import StringMixin, WarningsMixin


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


class QGridMinimalLabel(QLabel):
    def __init__(self, text: str, parent: QWidget | None = None):
        super().__init__(text, parent)

    def sizeHint(self) -> QSize:
        return QSize(-1, 15)


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


class SelectWordFromList(QDialog, StringMixin, WarningsMixin):
    def __init__(
        self,
        parent: QWidget,
        config: Config,
        win_title: str,
        words: list[str],
        callback: Callable[[tuple[str, str]], None],
        get_pair_callback: Callable[[str, int], tuple[str, str]],
        options: dict[str, Any] | None = None,
    ) -> None:
        """Dialog that lets the user select a word from a list of words.

        :param words: The list of candidate words

        :param callback: If the user selects a word, the callback is called to
        continue execution. The callback is given as an argument a pair of
        words. The first item of the pair is the selected word, the seconds item
        of the pair is determined by calling the ``get_pair_callback()`` function

        :param get_pair_callback: The callback is given the selected word and its
        index into the ``words`` array, and is expected to produce a pair of words
        as its return value

        :param options: A dictionary of options. The following options are available:
        * ``click_accept``: If True, the dialog is accepted when the user
           clicks on a word in the list. Default: False
        * ``close_on_accept``: If True, the dialog is closed when the user clicks
           the "Ok" button. Default: False
        """
        super().__init__(parent)
        self.config = config
        self.words = words
        self.ok_action = callback
        self.get_pair_callback = get_pair_callback
        if options is None:
            options = {}
        self.options = options
        self.button_config = self.config.config["Buttons"]
        self.window_config = self.config.config["SelectWordFromListWindow"]
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))
        self.setWindowTitle(win_title)
        self.header = CsvDatabaseHeader()
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
        def callback(text: str) -> None:
            self.edits[self.header.term1].setText(text)
            if self.check_bool_option("click_accept"):
                self.ok_button()

        self.scrollarea = QSelectItemScrollArea(
            items=self.words, select_callback=callback
        )
        layout.addWidget(self.scrollarea, vpos, 0, 1, 4)
        return

    def cancel_button(self) -> None:
        self.done(1)

    def check_bool_option(self, option: str) -> bool:
        if option in self.options:
            return typing.cast(bool, self.options[option])
        else:
            return False

    def check_term_in_list(self, term: str) -> bool:
        try:
            self.words.index(term)
        except ValueError:
            return False
        return True

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if (event is not None) and event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
            self.done(1)

    def ok_button(self) -> None:
        term1 = self.edits[self.header.term1].text()
        if self.check_space_or_empty_str(term1):
            self.display_warning(self, "Term1 is empty")
            return
        if not self.check_term_in_list(term1):
            self.display_warning(
                self,
                "Term1 is not a member of the list.\n"
                "Please choose an item from the list",
            )
            return
        self.edits[self.header.term1].setText("")
        if self.check_bool_option("close_on_accept"):
            self.done(0)
        idx = self.words.index(term1)
        pair = (self.get_pair_callback)(term1, idx)
        self.ok_action(pair)

    def update_scroll_area_items(self, text: str) -> None:
        self.scrollarea.update_items(text)
