import re

from PyQt6.QtCore import Qt
from pytest_mock.plugin import MockerFixture

from vocabuilder.modify_window import ModifyWindow
from vocabuilder.vocabuilder import MainWindow

from .common import QtBot


class TestGeneral:
    def test_cancel(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        dialog2 = ModifyWindow(dialog, "apple", dialog.config, window.db)
        idx = dialog2.button_names.index("&Cancel")
        cancel_button = dialog2.buttons[idx]
        with qtbot.waitSignal(dialog2.finished, timeout=1000):
            cancel_button.click()
        assert True

    def test_keypress_escape(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        dialog2 = ModifyWindow(dialog, "apple", dialog.config, window.db)
        with qtbot.waitSignal(dialog2.finished, timeout=1000):
            qtbot.keyClick(dialog2, Qt.Key.Key_Escape)
        assert True

    def test_term1_empty(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        dialog2 = ModifyWindow(dialog, "apple", dialog.config, window.db)
        dialog2.edits[dialog.header.term1].setText("")
        idx = dialog2.button_names.index("&Ok")
        ok_button = dialog2.buttons[idx]
        with qtbot.waitCallback() as callback:
            mocker.patch(
                "vocabuilder.mixins.WarningsMixin.display_warning",
                callback,
            )
            ok_button.click()
        msg = callback.args[1]
        assert re.search(r"Term1 is empty", msg)

    def test_term2_empty(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        dialog2 = ModifyWindow(dialog, "apple", dialog.config, window.db)
        dialog2.edits[dialog.header.term2].setText("")
        idx = dialog2.button_names.index("&Ok")
        ok_button = dialog2.buttons[idx]
        with qtbot.waitCallback() as callback:
            mocker.patch(
                "vocabuilder.mixins.WarningsMixin.display_warning",
                callback,
            )
            ok_button.click()
        msg = callback.args[1]
        assert re.search(r"Term2 is empty", msg)

    def test_old_term1_eq_new_term1(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        dialog2 = ModifyWindow(dialog, "apple", dialog.config, window.db)
        dialog2.edits[dialog.header.term2].setText("사과를")
        idx = dialog2.button_names.index("&Ok")
        ok_button = dialog2.buttons[idx]
        with qtbot.waitCallback() as callback:
            mocker.patch.object(dialog2.db, "update_item", callback)
            ok_button.click()
        assert len(callback.args) == 2

    def test_old_term1_ne_new_term1(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        dialog2 = ModifyWindow(dialog, "apple", dialog.config, window.db)
        dialog2.edits[dialog.header.term1].setText("apples")
        idx = dialog2.button_names.index("&Ok")
        ok_button = dialog2.buttons[idx]
        with qtbot.waitCallback() as callback:
            mocker.patch.object(dialog2.db, "modify_item", callback)
            ok_button.click()
        assert len(callback.args) == 2
