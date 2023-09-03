import logging

from PyQt6.QtCore import QCommandLineParser
from PyQt6.QtWidgets import QApplication

from vocabuilder.exceptions import CommandLineException


class CommandLineOptions:
    def __init__(self, app: QApplication) -> None:
        app.setApplicationName("VocaBuilder")
        app.setApplicationVersion("0.1")
        parser = QCommandLineParser()
        parser.addHelpOption()
        parser.addVersionOption()
        parser.addPositionalArgument("database", "Database to open")
        parser.process(app)
        arguments = parser.positionalArguments()
        logging.info(f"Commandline database argument: {arguments}")
        num_args = len(arguments)
        if num_args > 1:
            raise CommandLineException(
                "Bad command line arguments. Expected zero or one argument"
            )
        self.database_name: str | None
        if num_args == 1:
            self.database_name = arguments[0]
        else:
            self.database_name = None

    def get_database_name(self) -> str | None:
        return self.database_name
