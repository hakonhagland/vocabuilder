# import logging
# import re
# from PyQt6.QtCore import Qt
# from typing import Callable

from PyQt6.QtWidgets import QApplication
from pytest_mock.plugin import MockerFixture

import vocabuilder.vocabuilder

from .common import GetConfig


class TestGeneral:
    def test_set_options(
        self,
        get_config: GetConfig,
        mocker: MockerFixture,
        qapp: QApplication,
    ) -> None:
        cfg = get_config()
        mocker.patch(
            "vocabuilder.vocabuilder.platform.system",
            return_value="Darwin",
        )
        vocabuilder.vocabuilder.set_app_options(qapp, cfg)
        assert True
