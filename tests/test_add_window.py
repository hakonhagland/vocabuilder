import logging
import typing
from typing import Any, Callable

import pytest
from PyQt6.QtCore import Qt

# import re
from pytest_mock.plugin import MockerFixture

from vocabuilder.add_window import AddWindow
from vocabuilder.view_window import ViewWindow
from vocabuilder.vocabuilder import MainWindow

from .common import QtBot


class TestGeneral:
    @pytest.mark.parametrize("term1_exists", [True, False])
    def test_add_button(
        self,
        term1_exists: bool,
        main_window: MainWindow,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        window.add_new_entry()
        add_win = typing.cast(AddWindow, window.add_window)
        edit1 = add_win.edits[add_win.header.term1]
        edit1.setText("rose")
        if term1_exists:
            edit1.setText("apple")
            mocker.patch(
                "vocabuilder.mixins.WarningsMixin.display_warning",
                return_value=None,
            )
        edit2 = add_win.edits[add_win.header.term2]
        edit2.setText("장미")
        idx = add_win.button_names.index("&Add")
        add_button = add_win.buttons[idx]
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = add_win.add_button_pressed
                _self = add_win

                def wrapper(**kwargs: Any) -> None:
                    original_method(**kwargs)
                    callback(_self, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            add_button.clicked.disconnect()
            add_button.clicked.connect(wrapper)
            add_button.click()
        assert True

    @pytest.mark.parametrize("term1_exists", [True, False])
    def test_simulate_add_button(
        self,
        term1_exists: bool,
        main_window: MainWindow,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        window.add_new_entry()
        add_win = typing.cast(AddWindow, window.add_window)
        edit1 = add_win.edits[add_win.header.term1]
        edit1.setText("rose")
        if term1_exists:
            edit1.setText("apple")
            mocker.patch(
                "vocabuilder.mixins.WarningsMixin.display_warning",
                return_value=None,
            )
        edit2 = add_win.edits[add_win.header.term2]
        edit2.setText("장미")
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = add_win.simulate_add_button_pressed
                _self = add_win

                def wrapper(**kwargs: Any) -> None:
                    original_method(**kwargs)
                    callback(_self, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            edit2.returnPressed.disconnect()
            edit2.returnPressed.connect(wrapper)
            qtbot.keyPress(edit2, Qt.Key.Key_Enter, delay=100)
        assert True

    @pytest.mark.parametrize("view_edit2", [True, False])
    def test_add_update_view(
        self,
        view_edit2: bool,
        main_window: MainWindow,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        window.add_new_entry()
        add_win = typing.cast(AddWindow, window.add_window)
        window.view_entries()
        view_win = typing.cast(ViewWindow, window.view_window)
        view_edit = view_win.edit1
        view_method = view_win.update_items1
        view_text = "ap"
        if view_edit2:
            view_edit = view_win.edit2
            view_method = view_win.update_items2
            view_text = "가"
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = view_method

                def wrapper(*args: Any, **kwargs: Any) -> None:
                    original_method(*args, **kwargs)
                    callback(*args, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            view_edit.textChanged.disconnect()
            view_edit.textChanged.connect(wrapper)
            view_edit.setText(view_text)

        edit1 = add_win.edits[add_win.header.term1]
        edit1.setText("rose")
        edit2 = add_win.edits[add_win.header.term2]
        edit2.setText("장미")
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = add_win.simulate_add_button_pressed
                _self = add_win

                def wrapper(**kwargs: Any) -> None:
                    original_method(**kwargs)
                    callback(_self, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            edit2.returnPressed.disconnect()
            edit2.returnPressed.connect(wrapper)
            qtbot.keyPress(edit2, Qt.Key.Key_Enter, delay=100)
        assert True

    def test_cancel_button(
        self,
        main_window: MainWindow,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        window.add_new_entry()
        add_window = typing.cast(AddWindow, window.add_window)
        idx = add_window.button_names.index("&Cancel")
        cancel_button = add_window.buttons[idx]
        with qtbot.waitCallback() as callback:
            mocker.patch.object(add_window, "closeEvent", callback)
            cancel_button.click()
        assert True

    def test_keypress_escape(
        self,
        main_window: MainWindow,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        window.add_new_entry()
        add_window = typing.cast(AddWindow, window.add_window)
        with qtbot.waitCallback() as callback:
            mocker.patch.object(add_window, "closeEvent", callback)
            qtbot.keyClick(add_window, Qt.Key.Key_Escape)
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
        window.add_new_entry()
        add_win = typing.cast(AddWindow, window.add_window)
        edit1 = add_win.edits[add_win.header.term1]
        edit1.setText("rose")
        edit2 = add_win.edits[add_win.header.term2]
        edit2.setText("장미")
        if delay_str_empty:
            edit3 = add_win.edits[add_win.header.test_delay]
            edit3.setText("")
        idx = add_win.button_names.index("&Ok")
        ok_button = add_win.buttons[idx]
        if term1_exists or term1_empty or term2_empty:
            mocker.patch(
                "vocabuilder.mixins.WarningsMixin.display_warning",
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
                original_method = add_win.ok_button
                _self = add_win

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
        window.add_new_entry()
        add_win = typing.cast(AddWindow, window.add_window)
        edit = add_win.edits[add_win.header.term1]
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = add_win.update_scroll_area_items
                _self = add_win

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
        window.add_new_entry()
        add_win = typing.cast(AddWindow, window.add_window)
        label = add_win.scrollarea.labels[0]
        logging.info(f"scrollarea num_labels = {len(add_win.scrollarea.labels)}")
        edit = add_win.edits[add_win.header.term1]
        with qtbot.waitCallback() as callback:
            mocker.patch.object(edit, "setText", callback)
            qtbot.mouseClick(label, Qt.MouseButton.LeftButton)
        txt = callback.args[0]
        assert txt == "cloud"
