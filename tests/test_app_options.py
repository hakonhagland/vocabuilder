# import logging
# import re
# from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from pytest_mock.plugin import MockerFixture

import vocabuilder.vocabuilder
from vocabuilder.vocabuilder import Config


class TestGeneral:
    def test_set_options(
        self,
        config_object: Config,
        mocker: MockerFixture,
        qapp: QApplication,
    ) -> None:
        cfg = config_object
        mocker.patch(
            "vocabuilder.vocabuilder.platform.system",
            return_value="Darwin",
        )
        vocabuilder.vocabuilder.set_app_options(qapp, cfg)
        assert True
