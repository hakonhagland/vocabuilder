import logging
import pytest

# import re
from pytest_mock.plugin import MockerFixture
from PyQt6.QtCore import Qt
from vocabuilder.vocabuilder import (
    MainWindow,
)
from typing import Any, Callable
from .common import QtBot


class TestGeneral:
    def test_add_button(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        dialog = window.add_new_entry()
        idx = dialog.button_names.index("&Add")
        add_button = dialog.buttons[idx]
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = dialog.add_button_pressed
                _self = dialog

                def wrapper(**kwargs: Any) -> None:
                    original_method(**kwargs)
                    callback(_self, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            add_button.clicked.disconnect()
            add_button.clicked.connect(wrapper)
            add_button.click()
        assert True

    def test_cancel_button(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        dialog = window.add_new_entry()
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
        dialog = window.add_new_entry()
        with qtbot.waitSignal(dialog.finished, timeout=1000):
            qtbot.keyClick(dialog, Qt.Key.Key_Escape)
        assert True

    @pytest.mark.parametrize(
        "delay_str_empty, term1_exists, term1_empty, term2_empty",
        [
            (False, False, False, False),
            (True, False, False, False),
            (False, False, False, True),
            (False, False, True, False),
            (False, True, False, False),
        ],
    )
    def test_ok_button(
        self,
        delay_str_empty: bool,
        term1_exists: bool,
        term1_empty: bool,
        term2_empty: bool,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.add_new_entry()
        edit1 = dialog.edits[dialog.header.term1]
        edit1.setText("rose")
        edit2 = dialog.edits[dialog.header.term2]
        edit2.setText("장미")
        if delay_str_empty:
            edit3 = dialog.edits[dialog.header.test_delay]
            edit3.setText("")
        idx = dialog.button_names.index("&Ok")
        ok_button = dialog.buttons[idx]
        if term1_exists or term1_empty or term2_empty:
            mocker.patch(
                "vocabuilder.vocabuilder.WarningsMixin.display_warning",
                return_value=None,
            )
        if term1_exists:
            edit1.setText("apple")
        if term1_empty:
            edit1.setText("")
        if term2_empty:
            edit2.setText("")
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = dialog.ok_button
                _self = dialog

                def wrapper(**kwargs: Any) -> None:
                    original_method(**kwargs)
                    callback(_self, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            ok_button.clicked.disconnect()
            ok_button.clicked.connect(wrapper)
            ok_button.click()
        assert True

    def test_update_scroll_area(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        dialog = window.add_new_entry()
        edit = dialog.edits[dialog.header.term1]
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = dialog.update_scroll_area_items
                _self = dialog

                def wrapper(*args: Any, **kwargs: Any) -> None:
                    original_method(*args, **kwargs)
                    callback(_self, *args, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            edit.textChanged.disconnect()
            edit.textChanged.connect(wrapper)
            edit.setText("a")
        assert True

    def test_scroll_area_item_clicked(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog = window.add_new_entry()
        label = dialog.scrollarea.labels[0]
        logging.info(f"scrollarea num_labels = {len(dialog.scrollarea.labels)}")
        edit = dialog.edits[dialog.header.term1]
        with qtbot.waitCallback() as callback:
            mocker.patch.object(edit, "setText", callback)
            qtbot.mouseClick(label, Qt.MouseButton.LeftButton)
        txt = callback.args[0]
        assert txt == "bag"
