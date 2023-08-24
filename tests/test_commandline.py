# import logging
import pytest

# import re
from pytest_mock.plugin import MockerFixture

# from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication
from .common import QtBot
from vocabuilder.vocabuilder import CommandLineException, CommandLineOptions


class TestOk:
    test_args = ["db1"]

    @pytest.fixture(scope="session")
    def qapp_args(self) -> list[str]:
        return TestOk.test_args

    def test_main(
        self,
        mocker: MockerFixture,
        qapp: QApplication,
        qtbot: QtBot,
    ) -> None:
        mocker.patch(
            "vocabuilder.vocabuilder.QCommandLineParser.positionalArguments",
            return_value=TestOk.test_args,
        )
        args = CommandLineOptions(qapp)
        assert args.database_name == TestOk.test_args[0]


class TestBad:
    test_args = ["db1", "db2"]

    @pytest.fixture(scope="session")
    def qapp_args(self) -> list[str]:
        return TestBad.test_args

    def test_main(
        self,
        mocker: MockerFixture,
        qapp: QApplication,
        qtbot: QtBot,
    ) -> None:
        mocker.patch(
            "vocabuilder.vocabuilder.QCommandLineParser.positionalArguments",
            return_value=TestBad.test_args,
        )
        with pytest.raises(CommandLineException) as excinfo:
            CommandLineOptions(qapp)
        assert str(excinfo.value).startswith("Command line exception")
        # assert re.search(str(excinfo.value), "Expected")
