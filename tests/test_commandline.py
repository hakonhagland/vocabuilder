# import logging
import pytest

# from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication

# import re
from pytest_mock.plugin import MockerFixture

from vocabuilder.exceptions import CommandLineException
from vocabuilder.vocabuilder import CommandLineOptions


class TestGeneral:
    def test_ok(
        self,
        mocker: MockerFixture,
        qapp: QApplication,
    ) -> None:
        cmd_line_args = ["db1"]
        mocker.patch(
            "vocabuilder.commandline.QCommandLineParser.positionalArguments",
            return_value=cmd_line_args,
        )
        args = CommandLineOptions(qapp)
        assert args.database_name == cmd_line_args[0]

    def test_ok2(
        self,
        mocker: MockerFixture,
        qapp: QApplication,
    ) -> None:
        cmd_line_args: list[str] = []
        mocker.patch(
            "vocabuilder.commandline.QCommandLineParser.positionalArguments",
            return_value=cmd_line_args,
        )
        args = CommandLineOptions(qapp)
        assert args.database_name is None

    def test_bad(
        self,
        mocker: MockerFixture,
        qapp: QApplication,
    ) -> None:
        cmd_line_args = ["db1", "db2"]
        mocker.patch(
            "vocabuilder.commandline.QCommandLineParser.positionalArguments",
            return_value=cmd_line_args,
        )
        with pytest.raises(CommandLineException) as excinfo:
            CommandLineOptions(qapp)
        assert str(excinfo.value).startswith("Command line exception")
        # assert re.search(str(excinfo.value), "Expected")
