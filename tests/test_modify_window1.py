import re
from pytest_mock.plugin import MockerFixture
from PyQt6.QtCore import Qt
from vocabuilder.vocabuilder import (
    MainWindow,
)
from .common import QtBot


class TestGeneral:
    def test_cancel(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        idx = dialog.button_names.index("&Cancel")
        cancel_button = dialog.buttons[idx]
        with qtbot.waitSignal(dialog.finished, timeout=1000):
            cancel_button.click()
        assert True

    def test_keypress_escape(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        with qtbot.waitSignal(dialog.finished, timeout=1000):
            qtbot.keyClick(dialog, Qt.Key.Key_Escape)
        assert True


class TestModifyItem:
    def test_empty_str(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        idx = dialog.button_names.index("&Ok")
        ok_button = dialog.buttons[idx]
        with qtbot.waitCallback() as callback:
            mocker.patch(
                "vocabuilder.vocabuilder.WarningsMixin.display_warning",
                callback,
            )
            ok_button.click()
        msg = callback.args[1]
        assert re.search(r"Term1 is empty", msg)

    def test_nonexistent(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        dialog.edits[dialog.header.term1].setText("abcdefg")
        idx = dialog.button_names.index("&Ok")
        ok_button = dialog.buttons[idx]
        with qtbot.waitCallback() as callback:
            mocker.patch(
                "vocabuilder.vocabuilder.WarningsMixin.display_warning",
                callback,
            )
            ok_button.click()
        msg = callback.args[1]
        assert re.search(r"Term1 does not exist", msg)

    def test_valid(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        dialog.edits[dialog.header.term1].setText("apple")
        idx = dialog.button_names.index("&Ok")
        ok_button = dialog.buttons[idx]
        with qtbot.waitCallback() as callback:
            mocker.patch(
                "vocabuilder.vocabuilder.ModifyWindow2.open",
                callback,
            )
            ok_button.click()
        assert len(callback.args) == 0