import logging
import re
from _pytest.logging import LogCaptureFixture
from pytest_mock.plugin import MockerFixture
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QMessageBox
from vocabuilder.vocabuilder import (
    MainWindow,
)
from .common import QtBot


class TestConstructor:
    def test_ok(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        with qtbot.wait_exposed(window):
            assert len(window.buttons) == 6


class TestOther:
    def test_add(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        # with qtbot.wait_exposed(window):
        # idx = window.button_names['Add']
        # button = window.buttons[idx]
        # qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
        dialog = window.add_new_entry()
        # qtbot.add_widget(dialog)
        assert isinstance(dialog, QDialog)
        dialog.done(0)

    def test_create_backup(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        caplog: LogCaptureFixture,
    ) -> None:
        caplog.set_level(logging.INFO)
        window = main_window
        window.backup()
        # qtbot.wait(500)
        assert caplog.records[-1].msg.startswith("Created backup")

    def test_delete_entry(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        with qtbot.waitCallback() as callback:
            mocker.patch(
                "vocabuilder.vocabuilder.WarningsMixin.display_warning_callback",
                callback,
            )
            mbox = window.delete_entry()
            ok_button = mbox.button(QMessageBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.click()
        msg = callback.args[1]
        assert re.search(r"Delete entry", msg)

    def test_modify(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        dialog = window.modify_entry()
        assert isinstance(dialog, QDialog)
        dialog.done(0)

    def test_quit(
        self,
        main_window: MainWindow,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        mocker.patch.object(window, "app")
        window.quit()
        window.app.quit.assert_called()  # type: ignore

    def test_run_test(
        self,
        main_window: MainWindow,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        with qtbot.waitCallback() as callback:
            mocker.patch("vocabuilder.vocabuilder.TestWindow.main_dialog", callback)
            testwin = window.run_test()
            testwin.params.buttons[0].click()
        assert True

    def test_view_entries(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        with qtbot.waitCallback() as callback:
            mocker.patch(
                "vocabuilder.vocabuilder.WarningsMixin.display_warning_callback",
                callback,
            )
            mbox = window.view_entries()
            ok_button = mbox.button(QMessageBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.click()
        msg = callback.args[1]
        assert re.search(r"View entries", msg)


class TestKeyPressEvent:
    def test_press_b(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        with qtbot.waitCallback() as callback:
            mocker.patch.object(window, "backup", callback)
            qtbot.keyClick(window, Qt.Key.Key_B)
        assert True
