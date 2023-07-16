from PyQt6.QtWidgets import (
    QDialog,
)
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
        qtbot.add_widget(window)
        window.show()
        with qtbot.wait_exposed(window):
            assert len(window.buttons) == 6


class TestOther:
    def test_add(
        self,
        main_window: MainWindow,
        qtbot: QtBot,
    ) -> None:
        window = main_window
        qtbot.add_widget(window)
        window.show()
        # with qtbot.wait_exposed(window):
        # idx = window.button_names['Add']
        # button = window.buttons[idx]
        # qtbot.mouseClick(button, Qt.MouseButton.LeftButton)
        dialog = window.add_new_entry()
        qtbot.add_widget(dialog)
        assert isinstance(dialog, QDialog)
