import logging
import re
from typing import Any, Callable

import pytest
from _pytest.logging import LogCaptureFixture
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QMessageBox, QWidget
from pytest_mock.plugin import MockerFixture

from vocabuilder.exceptions import ConfigException
from vocabuilder.vocabuilder import MainWindow

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
        #        qtbot: QtBot,
    ) -> None:
        window = main_window
        window.add_new_entry()
        add_window = window.add_window
        assert isinstance(add_window, QWidget)
        # qtbot.add_widget(dialog)
        add_window.close()

    def test_re_activate_add(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
        # caplog: LogCaptureFixture
    ) -> None:
        # caplog.set_level(logging.INFO)
        window = main_window
        window.add_new_entry()
        add_win = window.add_window
        with qtbot.waitCallback() as callback:
            mocker.patch.object(add_win, "activateWindow", callback)
            window.add_new_entry()
        assert True

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
                "vocabuilder.mixins.WarningsMixin.display_warning_callback",
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
            mocker.patch("vocabuilder.test_window.TestWindow.main_dialog", callback)
            testwin = window.run_test()
            testwin.params.buttons[0].click()
        assert True

    def test_view_entries(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
        # caplog: LogCaptureFixture
    ) -> None:
        # caplog.set_level(logging.INFO)
        window = main_window
        window.view_entries()
        view_win = window.view_window
        callback_called = False

        def gen_wrapper() -> Callable[[Any, Any], None]:
            original_method = window.view_window_closed

            def wrapper(*args: Any, **kwargs: Any) -> None:
                nonlocal callback_called
                original_method(*args, **kwargs)
                callback_called = True

            return wrapper

        wrapper = gen_wrapper()
        mocker.patch.object(window, "view_window_closed", wrapper)
        qtbot.keyClick(view_win, Qt.Key.Key_Escape)
        qtbot.waitUntil(lambda: callback_called)
        assert True

    def test_re_activate_view(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
        # caplog: LogCaptureFixture
    ) -> None:
        # caplog.set_level(logging.INFO)
        window = main_window
        window.view_entries()
        view_win = window.view_window
        with qtbot.waitCallback() as callback:
            mocker.patch.object(view_win, "activateWindow", callback)
            window.view_entries()
        assert True


class TestMenuActions:
    @pytest.mark.parametrize("os_name", ["Linux", "Windows", "Darwin"])
    def test_edit_config(
        self,
        os_name: str,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        mocker.patch("vocabuilder.main_window.platform.system", return_value=os_name)
        with qtbot.waitCallback() as callback:
            mocker.patch("vocabuilder.main_window.subprocess.Popen", callback)
            window.edit_config_action.trigger()
        popen_arg = callback.args[0][0]
        if os_name == "Linux":
            assert popen_arg == "gedit"
        elif os_name == "Windows":
            assert popen_arg == "notepad.exe"
        elif os_name == "Darwin":
            assert popen_arg == "open"

    def test_edit_config_bad_os(
        self,
        main_window: MainWindow,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        mocker.patch("vocabuilder.main_window.platform.system", return_value="Unknown")
        with pytest.raises(ConfigException) as excinfo:
            window.edit_config()
        assert re.search(r"Unknown platform", str(excinfo))

    def test_reset_firebase(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        callback_called = False

        def gen_wrapper() -> Any:
            orig_method = window.db.firebase_database.run_reset

            def wrapper(*args: Any, **kwargs: Any) -> None:
                nonlocal callback_called
                orig_method(*args, **kwargs)
                callback_called = True

            return wrapper

        wrapper = gen_wrapper()
        mocker.patch.object(window.db.firebase_database, "run_reset", wrapper)
        window.reset_fb_action.trigger()
        qtbot.waitUntil(lambda: callback_called)
        assert True


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
