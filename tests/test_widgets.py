from pytest_mock.plugin import MockerFixture
from vocabuilder.vocabuilder import (
    MainWindow,
)
from vocabuilder.widgets import SelectWordFromList
from .common import QtBot


class TestSelectWordFromList:
    def test_select_from_list(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
        mocker: MockerFixture,
    ) -> None:
        window = main_window
        callback_called = False

        def callback(pair: tuple[str, str]) -> None:
            nonlocal callback_called
            word = pair[0]
            assert word == "apple"
            callback_called = True

        win_title = "Choose item to modify"
        items = window.db.get_term1_list()

        def get_pair_callback(word: str, idx: int) -> tuple[str, str]:
            return word, window.db.get_term2(word)

        # options = {"click_accept": False}
        options = None
        dialog = SelectWordFromList(
            window,
            window.config,
            win_title,
            items,
            callback,
            get_pair_callback,
            options,
        )
        dialog.edits[dialog.header.term1].setText("apple")
        idx = dialog.button_names.index("&Ok")
        ok_button = dialog.buttons[idx]
        ok_button.click()
        qtbot.waitUntil(lambda: callback_called)
        assert True
