import typing

import pytest
from typing import Any, Callable
from pytest_mock.plugin import MockerFixture
from PyQt6.QtCore import Qt
from vocabuilder.vocabuilder import MainWindow
from vocabuilder.view_window import ViewWindow
from vocabuilder.widgets import QLabelClickable
from .common import QtBot


class TestView:
    def test_callback(
        self,
        main_window: MainWindow,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        view_win: ViewWindow = window.view_entries()
        layout1 = view_win.scrollarea1.vbox
        assert layout1 is not None
        # item1 = layout1.itemAt(0) # The item at index 0 is the QSpacerItem
        item1 = layout1.itemAt(1)
        assert item1 is not None
        widget1 = item1.widget()
        assert widget1 is not None
        layout2 = widget1.layout()
        assert layout2 is not None
        item2 = layout2.itemAt(0)
        assert item2 is not None
        term1_label = item2.widget()
        assert term1_label is not None
        term1_label = typing.cast(QLabelClickable, term1_label)
        assert term1_label.text() == "bag"
        with qtbot.waitCallback() as callback:
            mocker.patch.object(view_win.edit1, "setText", callback)
            qtbot.mouseClick(term1_label, Qt.MouseButton.LeftButton)
        txt = callback.args[0]
        assert txt == "bag"

        item3 = layout2.itemAt(1)
        assert item3 is not None
        term2_label = item3.widget()
        assert term2_label is not None
        term2_label = typing.cast(QLabelClickable, term2_label)
        assert term2_label.text() == "가방"
        with qtbot.waitCallback() as callback:
            mocker.patch.object(view_win.edit2, "setText", callback)
            qtbot.mouseClick(term2_label, Qt.MouseButton.LeftButton)
        txt = callback.args[0]
        assert txt == "가방"

    @pytest.mark.parametrize("check1, check2", [(True, False), (False, True)])
    def test_set_text(
        self,
        check1: bool,
        check2: bool,
        main_window: MainWindow,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        view_win: ViewWindow = window.view_entries()
        callback_called = False

        def gen_wrapper() -> Callable[[Any, Any], None]:
            original_method = view_win.scrollarea1.add_items

            def wrapper(*args: Any, **kwargs: Any) -> None:
                nonlocal callback_called
                original_method(*args, **kwargs)
                callback_called = True

            return wrapper

        wrapper = gen_wrapper()
        mocker.patch.object(view_win.scrollarea1, "add_items", wrapper)
        if check1:
            view_win.edit1.setText("bag")
        if check2:
            view_win.edit2.setText("가방")
        qtbot.waitUntil(lambda: callback_called)
        assert True
