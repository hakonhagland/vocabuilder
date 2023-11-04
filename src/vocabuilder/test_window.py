from __future__ import annotations

# import logging
from typing import Callable
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIntValidator, QKeyEvent
from PyQt6.QtWidgets import (
    QDialog,
    QGridLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)
from vocabuilder.config import Config
from vocabuilder.constants import TestDirection, TestMethod
from vocabuilder.database import Database
from vocabuilder.mixins import WarningsMixin
from vocabuilder.widgets import SelectWordFromList


class TestWindow(QWidget, WarningsMixin):
    def __init__(self, parent: QWidget, config: Config, database: Database):
        super().__init__()
        self.db = database
        self.config = config
        self.window_config = self.config.config["TestWindow"]
        # NOTE: This complicated approach with callback is mainly done to make it easier
        #  to test the code with pytest
        self.params = TestWindowChooseParameters(
            parent, self, self.config, callback="main_dialog"
        )
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

    def assign_terms_to_practice(  # type: ignore
        self, callback: Callable[[], None] | Callable[[], TestWindow]
    ) -> None | TestWindow:
        """Determine the term to practice, either from a list of words, or select
        a word randomly.

        :param callback: called to continue execution after
           the term to practice has been determined. Note that the callback is needed
           since a non-blocking dialog will be opened if the term is selected from a list.
        """

        def callback2(pair: tuple[str, str] | None) -> None:
            if pair is None:
                self.display_warning_no_terms(self)
                self.close()
                return
            term1, term2 = pair
            self.term1 = term1
            self.term2 = term2
            if self.params.test_direction == TestDirection._1to2:
                self.lang1_term = self.term1
                self.lang2_term = self.term2
            else:
                self.lang1_term = self.term2
                self.lang2_term = self.term1
            callback()  # continue execution, see main_dialog2()

        if self.params.test_method == TestMethod.List:
            self.choose_word_from_list(callback=callback2)
        else:
            pair = self.db.get_random_pair()
            callback2(pair)

    def choose_word_from_list(
        self,
        callback: Callable[[tuple[str, str]], None],
    ) -> SelectWordFromList | None:
        """Choose a word to practice from a dialog showing a list of all words
        available for practice.

        :param callback: Callback to be called to continue execution after the
           the user has selected a word from the non-blocking dialog
        """
        pairs = self.db.get_pairs_exceeding_test_delay()
        if len(pairs) > 0:
            if self.params.test_direction == TestDirection._1to2:
                idx1 = 0
                idx2 = 1
            else:
                idx1 = 1
                idx2 = 0
            words = [item[idx1] for item in pairs]

            def get_pair(word: str, idx: int) -> tuple[str, str]:
                """given a word and an index, recover the pair of words to be
                practiced"""
                return word, pairs[idx][idx2]

            # NOTE: it is assumed that callback function holds a reference to
            #       self, such that self will not be garbage collected until
            #       the callback is done
            title = "Select word to practice"
            options = {"click_accept": True, "close_on_accept": True}
            return SelectWordFromList(
                self, self.config, title, words, callback, get_pair, options
            )
        self.display_warning_no_terms(self)
        return None

    def done_button_clicked(self) -> None:
        delay = self.delay_edit.text()
        self.db.update_retest_value(self.term1, int(delay))
        self.close()

    def keyPressEvent(self, event: QKeyEvent | None) -> None:
        # print(f"key code: {event.key()}, text: {event.text()}")
        if (event is not None) and event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
            self.close()

    def main_dialog(self) -> None:
        """This is a callback method which is called after the test parameters has
        been chosen from the ``TestWindowChooseParameters`` dialog"""

        if self.params.cancelled:
            return None
        # NOTE: asssign_terms_to_practice() might open a new dialog window, so
        #   we need to pass it a callback such that execution can be continued
        #   in main_dialog2() at a later time. (We are using these nonblocking
        #   dialogs because it makes it easier to write unit tests)
        self.assign_terms_to_practice(callback=self.main_dialog2)

    def main_dialog2(self) -> TestWindow:
        """This is a callback that is called after the current pair of words
        to practice has been assigned"""
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
        self.show()
        return self

    def next_button_clicked(self) -> None:
        delay = self.delay_edit.text()
        self.db.update_retest_value(self.term1, int(delay))

        def callback() -> None:
            self.term1_label.setText(self.lang1_term)
            self.hidden_label.setText(self.config.config["Practice"]["HiddenText"])
            self.hidden_toggle = True
            self.user_edit.setText("")
            self.user_edit.setFocus()

        self.assign_terms_to_practice(callback=callback)

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
    def __init__(
        self, main_window: QWidget, parent: TestWindow, config: Config, callback: str
    ) -> None:
        super().__init__(main_window)  # make dialog modal
        self.testwin_callback = callback
        self.testwin = parent
        self.config = config
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

    # fmt: off
    def keyPressEvent(self, event: QKeyEvent | None) -> None:  # noqa: C901
        # print(f"key code: {event.key()}, text: {event.text()}")
        if event is not None:
            if event.key() == Qt.Key.Key_Escape:  # "ESC" pressed
                self.cancel_button()
            if event.key() == Qt.Key.Key_L:
                def callback() -> None:
                    self.random_button.setChecked(False)
                    self.choose_from_list_button.setChecked(True)
                self.modify_checkbox_group1(callback)
            elif event.key() == Qt.Key.Key_R:
                def callback() -> None:
                    self.random_button.setChecked(True)
                    self.choose_from_list_button.setChecked(False)
                self.modify_checkbox_group1(callback)
            elif event.key() == Qt.Key.Key_1:
                def callback() -> None:
                    self.lang1to2_button.setChecked(True)
                    self.lang2to1_button.setChecked(False)
                self.modify_checkbox_group2(callback)
            elif event.key() == Qt.Key.Key_2:
                def callback() -> None:
                    self.lang2to1_button.setChecked(True)
                    self.lang1to2_button.setChecked(False)
                self.modify_checkbox_group2(callback)
    # fmt: on

    def modify_checkbox_group1(self, callback: Callable[[], None]) -> None:
        self.random_button.setAutoExclusive(False)
        self.choose_from_list_button.setAutoExclusive(False)
        callback()
        self.random_button.setAutoExclusive(True)
        self.choose_from_list_button.setAutoExclusive(True)

    def modify_checkbox_group2(self, callback: Callable[[], None]) -> None:
        self.lang1to2_button.setAutoExclusive(False)
        self.lang2to1_button.setAutoExclusive(False)
        callback()
        self.lang1to2_button.setAutoExclusive(True)
        self.lang2to1_button.setAutoExclusive(True)

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
