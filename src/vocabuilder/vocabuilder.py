#! /usr/bin/env python3
from __future__ import annotations

import logging
import platform  # determine os name

# import pdb
import sys

# from pprint import pprint

# NOTE: "Self" type requires python >= 3.11, and we are trying to support python 3.10, so
#   we will work around this using "from __future__ import annotations", see above
#   See also: https://stackoverflow.com/a/33533514/2173773
# from typing_extensions import Self

from PyQt6 import QtGui
from PyQt6.QtWidgets import QApplication

from vocabuilder.exceptions import SelectVocabularyException
from vocabuilder.commandline import CommandLineOptions
from vocabuilder.config import Config
from vocabuilder.database import Database
from vocabuilder.main_window import MainWindow
from vocabuilder.select_voca import SelectVocabulary

# NOTE: type hints for collection of builtin types requires python>=3.9, see
#  https://mypy.readthedocs.io/en/stable/cheat_sheet_py3.html
# NOTE: type hints using union types (using pipe only), e.g. "str | None",
#   requires python >= 3.10
#   see: https://docs.python.org/3/library/stdtypes.html#types-union
MIN_PYTHON = (3, 10)
if sys.version_info < MIN_PYTHON:  # pragma: no cover
    sys.exit(f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]} or later is required.")


def select_vocabulary(opts: CommandLineOptions, cfg: Config, app: QApplication) -> str:
    """The user can select between different databases with different vocabularies"""
    select = SelectVocabulary(opts, cfg, app)
    name = select.get_name()
    if name is None:
        raise SelectVocabularyException("No vocabulary name given")
    return name


def set_app_options(app: QApplication, cfg: Config) -> None:
    if platform.system() == "Darwin":
        enable = cfg.config.getboolean("MacOS", "EnableAmpersandShortcut")
        QtGui.qt_set_sequence_auto_mnemonic(enable)


def main() -> None:
    # logging.basicConfig(
    #     filename='/tmp/vb.log',
    #     filemode='w',
    #     level=logging.DEBUG,
    # )
    logging.basicConfig(level=logging.INFO)
    app = QApplication(sys.argv)
    # options = CommandLineOptions(app)
    cmdline_opts = CommandLineOptions(app)
    config = Config()
    voca_name = select_vocabulary(cmdline_opts, config, app)
    db = Database(config, voca_name)
    set_app_options(app, config)
    window = MainWindow(app, db, config)
    window.show()
    app.exec()


if __name__ == "__main__":  # pragma: no cover
    main()
