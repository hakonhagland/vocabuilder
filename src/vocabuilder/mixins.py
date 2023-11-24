import time
from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMessageBox, QWidget

from vocabuilder.exceptions import TimeException


class ConfigWindow:  # pragma: no cover
    window_config: dict[str, str]

    def move(self, x: int, y: int) -> None:
        ...

    def resize(self, w: int, h: int) -> None:
        ...


class ResizeWindowMixin(ConfigWindow):
    def resize_window_from_config(self: ConfigWindow) -> None:
        if ("X" in self.window_config) and ("Y" in self.window_config):
            self.move(
                int(self.window_config["X"]),
                int(self.window_config["Y"]),
            )
        self.resize(int(self.window_config["Width"]), int(self.window_config["Height"]))


class StringMixin:
    """String methods"""

    @staticmethod
    def check_space_or_empty_str(str_: str) -> bool:
        """Is string empty or only space characters?

        :param str str_: Input string
        :return: True if string is empty or only space"""

        if len(str_) == 0 or str_.isspace():
            return True
        return False


class TimeMixin:
    @staticmethod
    def epoch_in_seconds() -> int:
        return int(time.time())

    @staticmethod
    def get_epoch_diff_in_days(t1: int, t2: int) -> int:
        """t1, t2: epoch times. In general these times could be negative, but
        in this application they should always be positive (corresponding to
        dates after year 2022)"""
        if t1 > t2:
            raise TimeException(
                "Bad timestamp. Smaller than previous timestamp. Expected larger"
            )
        diff = (t2 - t1) // (24 * 60 * 60)
        return diff


class WarningsMixin:
    @staticmethod
    def display_warning(
        parent: QWidget, msg: str, callback: Callable[[], None] | None = None
    ) -> QMessageBox:
        mbox = QMessageBox(
            parent
        )  # giving "parent" makes the message box appear centered on the parent
        mbox.setIcon(QMessageBox.Icon.Information)
        mbox.setText(msg)
        # mbox.setInformativeText("This is additional information")
        mbox.setWindowTitle("Warning")
        # mbox.setDetailedText("The details are as follows:")
        mbox.setStandardButtons(QMessageBox.StandardButton.Ok)
        mbox.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, True)
        if callback is None:

            def button_clicked() -> None:
                WarningsMixin.display_warning_callback(mbox, msg)

            callback = button_clicked
        mbox.open(callback)
        return mbox

    @staticmethod
    def display_warning_no_terms(
        parent: QWidget, callback: Callable[[], None] | None = None
    ) -> QMessageBox:
        return WarningsMixin.display_warning(
            parent,
            "No terms ready for practice today!\n"
            "That is: no terms with expired date left in database\n"
            "Note: You can override the date check in the settings menu.",
            callback,
        )

    @staticmethod
    def display_warning_callback(
        mbox: QMessageBox, msg: str
    ) -> None:  # pragma: no cover
        """This method is here such that it can be mocked from pytest"""
        pass
