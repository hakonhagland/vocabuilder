import logging
import pytest
import re
from _pytest.logging import LogCaptureFixture
from pytest_mock.plugin import MockerFixture
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QDialog, QMessageBox
from typing import Any, Callable
from vocabuilder.vocabuilder import (
    MainWindow,
)
from vocabuilder.exceptions import ConfigException
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
        dialog = window.add_new_entry()
        assert isinstance(dialog, QDialog)
        # qtbot.add_widget(dialog)
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
    ) -> None:
        window = main_window
        with qtbot.waitCallback() as callback:
            mocker.patch(
                "vocabuilder.mixins.WarningsMixin.display_warning_callback",
                callback,
            )
            mbox = window.view_entries()
            ok_button = mbox.button(QMessageBox.StandardButton.Ok)
            if ok_button is not None:
                ok_button.click()
        msg = callback.args[1]
        assert re.search(r"View entries", msg)


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
        execvp_mock = mocker.MagicMock()
        callback_called = False

        def gen_wrapper() -> Any:
            orig_method = window.run_task

            def wrapper(
                orig_task: Callable[[str, list[str]], None], cmd: str, args: list[str]
            ) -> None:
                nonlocal callback_called
                nonlocal execvp_mock
                mock = mocker.MagicMock()
                mocker.patch("vocabuilder.main_window.multiprocessing.Process", mock)
                mocker.patch("vocabuilder.main_window.os.execvp", execvp_mock)
                orig_method(orig_task, cmd, args)
                callback_called = True
                orig_task(cmd, args)
                callback_called = True

            return wrapper

        wrapper = gen_wrapper()
        mocker.patch.object(window, "run_task", wrapper)
        # window.edit_config_action.disconnect()
        # window.edit_config_action.triggered.connect(wrapper)
        window.edit_config_action.trigger()
        qtbot.waitUntil(lambda: callback_called)
        execvp_args = execvp_mock.call_args.args
        if os_name == "Linux":
            assert execvp_args[0] == "gedit"
        elif os_name == "Windows":
            assert execvp_args[0] == "notepad.exe"
        elif os_name == "Darwin":
            assert execvp_args[0] == "open"

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
