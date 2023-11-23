import re

from PyQt6.QtCore import Qt
from pytest_mock.plugin import MockerFixture

from vocabuilder.vocabuilder import MainWindow

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
                "vocabuilder.mixins.WarningsMixin.display_warning",
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
                "vocabuilder.mixins.WarningsMixin.display_warning",
                callback,
            )
            ok_button.click()
        msg = callback.args[1]
        assert re.search(r"Term1 is not a member of the list", msg)

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
                "vocabuilder.modify_window.ModifyWindow.open",
                callback,
            )
            ok_button.click()
        assert len(callback.args) == 0

    def test_scroll_area_item_clicked(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        label = dialog.scrollarea.labels[0]
        edit = dialog.edits[dialog.header.term1]
        with qtbot.waitCallback() as callback:
            mocker.patch.object(edit, "setText", callback)
            qtbot.mouseClick(label, Qt.MouseButton.LeftButton)
        txt = callback.args[0]
        assert txt == "bag"
