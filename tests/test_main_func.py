# import logging
# import pytest

# import re
from pathlib import Path
from pytest_mock.plugin import MockerFixture

# from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
import vocabuilder.vocabuilder as vocab
from .common import PytestDataDict, QtBot
from typing import Callable


class TestMain:
    def test_main(
        self,
        config_dir_path: Path,
        mocker: MockerFixture,
        data_dir_path: Path,
        test_data: PytestDataDict,
        setup_database_dir: Callable[[], Path],
        qapp: QApplication,
        qtbot: QtBot,
    ) -> None:
        cfg_dir = config_dir_path
        data_dir = data_dir_path
        mocker.patch(
            "vocabuilder.vocabuilder.platformdirs.user_config_dir",
            return_value=cfg_dir,
        )
        mocker.patch(
            "vocabuilder.vocabuilder.platformdirs.user_data_dir",
            return_value=data_dir,
        )
        setup_database_dir()
        mocker.patch(
            "vocabuilder.vocabuilder.select_vocabulary",
            return_value=test_data["vocaname"],
        )
        mocker.patch(
            "vocabuilder.vocabuilder.QApplication",
            return_value=qapp,
        )
        with qtbot.waitCallback() as callback:
            mocker.patch.object(qapp, "exec", callback)
            vocab.main()
        assert True
