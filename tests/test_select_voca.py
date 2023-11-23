# import logging
import re
import shutil
from pathlib import Path
from typing import Callable

import pytest
from PyQt6.QtWidgets import QApplication
from pytest_mock.plugin import MockerFixture

import vocabuilder.vocabuilder
from vocabuilder.local_database import LocalDatabase
from vocabuilder.select_voca import SelectNewVocabularyName
from vocabuilder.vocabuilder import (
    CommandLineOptions,
    Config,
    SelectVocabularyException,
)

from .common import QtBot

# from .conftest import config_object, config_dir_path


class TestGeneral:
    @pytest.mark.parametrize(
        "cmdline_arg, voca_exists, info_fn_exists",
        [
            (True, True, True),
            (False, False, False),
            (False, False, True),
            (False, True, True),
        ],
    )
    def test_construct(
        self,
        cmdline_arg: bool,
        voca_exists: bool,
        info_fn_exists: bool,
        qapp: QApplication,
        config_object: Config,
        setup_database_dir: Callable[[], Path],
        mocker: MockerFixture,
    ) -> None:
        app = qapp
        cfg = config_object
        opts = CommandLineOptions(qapp)
        datadir = setup_database_dir()
        if not cmdline_arg:
            mocker.patch.object(opts, "get_database_name", return_value=None)
        if not voca_exists:
            mocker.patch.object(app, "exec", return_value=None)
            mocker.patch("builtins.quit", return_value=None)
            shutil.rmtree(datadir)
        if not info_fn_exists:
            fn = cfg.get_config_dir() / LocalDatabase.active_voca_info_fn
            fn.unlink()
        if not cmdline_arg and not voca_exists:
            with pytest.raises(SelectVocabularyException) as excinfo:
                name = vocabuilder.vocabuilder.select_vocabulary(opts, cfg, app)
            assert re.search(r"No vocabulary name", str(excinfo))
        else:
            name = vocabuilder.vocabuilder.select_vocabulary(opts, cfg, app)
            assert name == "english-korean"

    @pytest.mark.parametrize(
        "cmdline_param, most_recent, db_exist",
        [
            (None, False, True),
            ("english-korean", False, True),
            ("english-korean", True, True),
            (None, True, True),
            (None, True, False),
        ],
    )
    def test_no_args(
        self,
        cmdline_param: str | None,
        most_recent: bool,
        db_exist: bool,
        qapp: QApplication,
        config_object: Config,
        mocker: MockerFixture,
        setup_database_dir: Callable[[], Path],
    ) -> None:
        app = qapp
        cfg = config_object
        retval = cmdline_param
        patch_retval: str | None = "english-korean"
        if db_exist:
            setup_database_dir()
            patch_retval = cmdline_param
        if most_recent:
            retval = "english-korean"
        else:
            fn = cfg.get_config_dir() / LocalDatabase.active_voca_info_fn
            fn.unlink()
            if cmdline_param is None:
                retval = "english-korean"

        opts = CommandLineOptions(qapp)
        mocker.patch.object(opts, "get_database_name", return_value=None)
        mocker.patch("builtins.quit", return_value=None)
        mocker.patch(
            "vocabuilder.vocabuilder.SelectVocabulary.open_select_voca_window",
            return_value=patch_retval,
        )
        name = vocabuilder.vocabuilder.select_vocabulary(opts, cfg, app)
        assert name == retval

    @pytest.mark.parametrize(
        "valid_name, bad_char", [(True, False), (False, False), (False, True)]
    )
    def test_select_name_window(
        self,
        valid_name: bool,
        bad_char: bool,
        qapp: QApplication,
        config_object: Config,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        app = qapp
        cfg = config_object
        win = SelectNewVocabularyName(cfg, app)
        win.show()
        qtbot.add_widget(win)
        idx = win.button_names.index("&Ok")
        ok_button = win.buttons[idx]
        with qtbot.waitCallback() as callback:
            if not valid_name:
                mocker.patch(
                    "vocabuilder.mixins.WarningsMixin.display_warning",
                    callback,
                )
            else:
                win.line_edit.setText("english-korean")
                mocker.patch.object(app, "exit", callback)
            if bad_char:
                win.line_edit.setText("english/korean")
            ok_button.click()
        if not valid_name:
            msg = callback.args[1]
            if bad_char:
                assert re.search("cannot contain slashes", msg)
            else:
                assert re.search("name is empty", msg)
        else:
            assert True

    def test_select_name_window_cancel(
        self,
        qapp: QApplication,
        config_object: Config,
        mocker: MockerFixture,
        qtbot: QtBot,
    ) -> None:
        app = qapp
        cfg = config_object
        win = SelectNewVocabularyName(cfg, app)
        qtbot.add_widget(win)
        win.show()
        idx = win.button_names.index("&Cancel")
        cancel_button = win.buttons[idx]
        with qtbot.waitCallback() as callback:
            mocker.patch.object(app, "exit", callback)
            cancel_button.click()
        assert True
