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
