# import re
# import logging
import pytest
from pytest_mock.plugin import MockerFixture

from PyQt6.QtCore import Qt
from vocabuilder.vocabuilder import MainWindow
from vocabuilder.vocabuilder import (
    TestWindow as _TestWindow,
)  # Cannot start with "Test"
from .common import QtBot
from typing import Any, Callable


class TestGeneral:
    @pytest.mark.parametrize(
        "button_name, pair, original_test_direction, choose_random",
        [
            ("&Ok", True, True, True),
            ("&Cancel", True, True, True),
            ("&Ok", False, True, True),
            ("&Ok", True, False, False),
        ],
    )
    def test_main_dialog(
        self,
        button_name: str,
        pair: bool,
        original_test_direction: bool,
        choose_random: bool,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        with qtbot.waitCallback() as callback:
            testwin = window.run_test()

            def gen_wrapper() -> Callable[[], None]:
                # original_method = _TestWindow.main_dialog
                original_method = testwin.main_dialog
                _self = testwin

                def wrapper(*args: Any, **kwargs: Any) -> None:
                    original_method(*args, **kwargs)
                    callback(_self, *args, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            # TODO: I was not able to use mocker.patch... on main_dialog() due to issues with
            #  bound/unbound methods, autospec=False/autospec=True, wraps=... , see e.g.
            #  https://docs.python.org/3/library/unittest.mock-examples.html#mocking-unbound-methods
            #  https://github.com/python/cpython/issues/75988
            #  So I am going to mock manually here for now..
            testwin.main_dialog = wrapper  # type: ignore
            if not pair:
                mocker.patch(
                    "vocabuilder.vocabuilder.Database.get_random_pair",
                    return_value=None,
                )
            idx = testwin.params.button_names.index(button_name)
            if not original_test_direction:
                testwin.params.lang1to2_button.setAutoExclusive(False)
                testwin.params.lang1to2_button.setChecked(False)
                testwin.params.lang2to1_button.setChecked(True)
                testwin.params.lang1to2_button.setAutoExclusive(True)
            if not choose_random:
                testwin.params.random_button.setAutoExclusive(False)
                testwin.params.random_button.setChecked(False)
                testwin.params.choose_from_list_button.setChecked(True)
                testwin.params.random_button.setAutoExclusive(True)
            testwin.params.buttons[idx].click()
        assert True

    def test_done_button(
        self,
        test_window: _TestWindow,
        qtbot: QtBot,
    ) -> None:
        testwin = test_window
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = testwin.done_button_clicked
                _self = testwin

                def wrapper(**kwargs: Any) -> None:
                    original_method(**kwargs)
                    callback(_self, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            # TODO: see comment for test_main_dialog() above
            testwin.done_button_clicked = wrapper  # type: ignore
            testwin.done_button.clicked.disconnect()
            testwin.done_button.clicked.connect(wrapper)
            testwin.done_button.click()
        assert True

    def test_keypress_esc(
        self,
        test_window: _TestWindow,
        qtbot: QtBot,
    ) -> None:
        testwin = test_window
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = testwin.keyPressEvent
                _self = testwin

                def wrapper(*args: Any, **kwargs: Any) -> None:
                    original_method(*args, **kwargs)
                    callback(_self, *args, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            # TODO: see comment for test_main_dialog() above
            testwin.keyPressEvent = wrapper  # type: ignore
            qtbot.keyClick(testwin, Qt.Key.Key_Escape)
        assert True

    @pytest.mark.parametrize("pair", [True, False])
    def test_next_button(
        self,
        pair: bool,
        test_window: _TestWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        testwin = test_window
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = testwin.next_button_clicked
                _self = testwin

                def wrapper(**kwargs: Any) -> None:
                    original_method(**kwargs)
                    callback(_self, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            # TODO: see comment for test_main_dialog() above
            testwin.next_button_clicked = wrapper  # type: ignore
            testwin.next_button.clicked.disconnect()
            testwin.next_button.clicked.connect(wrapper)
            if not pair:
                mocker.patch(
                    "vocabuilder.vocabuilder.Database.get_random_pair",
                    return_value=None,
                )
            testwin.next_button.click()
        assert True

    @pytest.mark.parametrize("toggle", [True, False])
    def test_show_hidden(
        self,
        toggle: bool,
        test_window: _TestWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        testwin = test_window
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = testwin.show_hidden_button_callback
                _self = testwin

                def wrapper(**kwargs: Any) -> None:
                    original_method(**kwargs)
                    callback(_self, **kwargs)

                return wrapper

            # TODO: see comment for test_main_dialog() above
            wrapper = gen_wrapper()
            testwin.show_hidden_button.clicked.disconnect()
            testwin.show_hidden_button.clicked.connect(wrapper)
            testwin.hidden_toggle = toggle
            testwin.show_hidden_button.click()
        assert True

    def test_retest_button(
        self,
        test_window: _TestWindow,
        qtbot: QtBot,
    ) -> None:
        testwin = test_window
        button_idx = 2
        with qtbot.waitCallback() as callback:

            def gen_wrapper() -> Callable[[], None]:
                original_method = testwin.retest_button_callbacks[button_idx]
                _self = testwin

                def wrapper(**kwargs: Any) -> None:
                    original_method(**kwargs)
                    callback(_self, **kwargs)

                return wrapper

            # TODO: see comment for test_main_dialog() above
            wrapper = gen_wrapper()
            testwin.retest_buttons[button_idx].clicked.disconnect()
            testwin.retest_buttons[button_idx].clicked.connect(wrapper)
            testwin.retest_buttons[button_idx].click()
        assert True
