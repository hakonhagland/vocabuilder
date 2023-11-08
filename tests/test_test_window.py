# import re
# import logging
import platform
import pytest
import typing
from pytest_mock.plugin import MockerFixture

from PyQt6.QtCore import Qt
from vocabuilder.test_window import (
    TestWindow as _TestWindow,
)  # Cannot start with "Test"
from vocabuilder.widgets import SelectWordFromList
from vocabuilder.vocabuilder import MainWindow
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
        if (not pair) and (platform.system() == "Darwin"):  # pragma: no cover
            # This test with "pair == False" segfaults for some reason on macOS
            # TODO: look into this
            pytest.skip("Skipping test on macOS that segfaults. TODO: Look into this.")
            return
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
                    "vocabuilder.local_database.LocalDatabase.get_random_pair",
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

    @pytest.mark.parametrize(
        "keycode, ok_button",
        [
            (Qt.Key.Key_R, True),
            (Qt.Key.Key_L, True),
            (Qt.Key.Key_1, True),
            (Qt.Key.Key_2, False),
        ],
    )
    def test_click_param_radio_buttons(
        self,
        keycode: Qt.Key,
        ok_button: bool,
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
            testwin.main_dialog = wrapper  # type: ignore
            if ok_button:
                idx = testwin.params.button_names.index("&Ok")
                qtbot.keyClick(testwin.params, keycode)
                testwin.params.buttons[idx].click()
            else:
                qtbot.keyClick(testwin.params, keycode)
                qtbot.keyClick(testwin.params, Qt.Key.Key_Escape)

        assert True

    def test_main_dialog2(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        with qtbot.waitCallback() as callback:
            testwin = window.run_test()

            def gen_wrapper() -> Callable[[], None]:
                # original_method = _TestWindow.main_dialog
                original_method = testwin.main_dialog2
                _self = testwin

                def wrapper(*args: Any, **kwargs: Any) -> None:
                    original_method(*args, **kwargs)
                    callback(_self, *args, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            # TODO: See comment for test_main_dialog()
            testwin.main_dialog2 = wrapper  # type: ignore
            idx = testwin.params.button_names.index("&Ok")
            testwin.params.lang1to2_button.setAutoExclusive(False)
            testwin.params.lang1to2_button.setChecked(False)
            testwin.params.lang2to1_button.setChecked(True)
            testwin.params.lang1to2_button.setAutoExclusive(True)
            testwin.params.buttons[idx].click()
        assert True

    @pytest.mark.parametrize(
        "valid_pair,click_label", [(True, False), (False, False), (True, True)]
    )
    def test_select_from_list(
        self,
        valid_pair: bool,
        click_label: bool,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        dialog: SelectWordFromList | None = None
        callback3: Callable[[tuple[str, str]], None] | None = None
        with qtbot.waitCallback() as callback:
            testwin = window.run_test()
            if not valid_pair:
                mocker.patch.object(
                    testwin.db,
                    "get_pairs_exceeding_test_delay",
                    return_value=[],
                )

            def gen_wrapper() -> Callable[[], None]:
                # original_method = _TestWindow.main_dialog
                original_method = testwin.choose_word_from_list
                _self = testwin

                def wrapper(*args: Any, **kwargs: Any) -> None:
                    nonlocal dialog
                    nonlocal callback3
                    callback3 = kwargs["callback"]
                    dialog = original_method(*args, **kwargs)
                    callback(_self, *args, **kwargs)

                return wrapper

            wrapper = gen_wrapper()
            # TODO: See comment for test_main_dialog()
            testwin.choose_word_from_list = wrapper  # type: ignore
            idx = testwin.params.button_names.index("&Ok")
            testwin.params.random_button.setAutoExclusive(False)
            testwin.params.random_button.setChecked(False)
            testwin.params.choose_from_list_button.setChecked(True)
            testwin.params.random_button.setAutoExclusive(True)
            testwin.params.buttons[idx].click()
        if dialog is not None:
            if click_label:
                with qtbot.waitCallback() as callback2:
                    dialog.ok_action = callback2
                    label = dialog.scrollarea.labels[2]
                    qtbot.mouseClick(label, Qt.MouseButton.LeftButton)
            else:
                idx = dialog.button_names.index("&Ok")
                ok_button = dialog.buttons[idx]
                dialog.edits[dialog.header.term1].setText("apple")
                with qtbot.waitCallback() as callback2:
                    dialog.ok_action = callback2
                    ok_button.click()
            pair = callback2.args[0]
            assert len(pair) == 2
            assert pair[1] == "사과"
            callback3 = typing.cast(Callable[[tuple[str, str]], None], callback3)
            callback3(pair)

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
                    "vocabuilder.local_database.LocalDatabase.get_random_pair",
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
