import typing
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
        layout = view_win.scrollarea1.layout_
        assert layout is not None
        item1 = layout.itemAt(0)
        assert item1 is not None
        term1_label = item1.widget()
        assert term1_label is not None
        term1_label = typing.cast(QLabelClickable, term1_label)
        assert term1_label.text() == "100,000,000"
        with qtbot.waitCallback() as callback:
            mocker.patch.object(view_win.edit1, "setText", callback)
            qtbot.mouseClick(term1_label, Qt.MouseButton.LeftButton)
        txt = callback.args[0]
        assert txt == "100,000,000"
        item2 = layout.itemAt(1)
        assert item2 is not None
        term2_label = item2.widget()
        assert term2_label is not None
        term2_label = typing.cast(QLabelClickable, term2_label)
        assert term2_label.text() == "억"
        with qtbot.waitCallback() as callback:
            mocker.patch.object(view_win.edit2, "setText", callback)
            qtbot.mouseClick(term2_label, Qt.MouseButton.LeftButton)
        txt = callback.args[0]
        assert txt == "억"
