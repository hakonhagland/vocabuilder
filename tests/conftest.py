import shutil
import typing
import pytest

from pathlib import Path
from pytest_mock.plugin import MockerFixture
from typing import Any, Callable
from PyQt6.QtWidgets import (
    QApplication,
)

from vocabuilder.vocabuilder import Config, Database, MainWindow, SelectVocabulary
from vocabuilder.vocabuilder import TestWindow as _TestWindow
from .common import PytestDataDict, QtBot


# This will override all qapp_args in all tests since it is session scoped
@pytest.fixture(scope="session")
def qapp_args() -> list[str]:
    return ["vocabuilder", "english-korean"]


@pytest.fixture(scope="session")
def test_file_path() -> Path:
    return Path(__file__).parent / "files"


@pytest.fixture(scope="session")
def test_data() -> PytestDataDict:
    return {
        "config_dir": "config",
        "data_dir": "data",
        "vocaname": "english-korean",
    }


@pytest.fixture()
def data_dir_path(
    tmp_path: Path, test_file_path: Path, test_data: PytestDataDict
) -> Path:
    data_dir = tmp_path / test_data["data_dir"]
    data_dir.mkdir()
    data_dirlock_fn = test_file_path / test_data["data_dir"] / Config.dirlock_fn
    shutil.copy(data_dirlock_fn, data_dir)
    return data_dir


@pytest.fixture()
def config_dir_path(
    test_file_path: Path,
    test_data: PytestDataDict,
    tmp_path: Path,
) -> Path:
    cfg_dir_src = test_file_path / test_data["config_dir"]
    cfg_dir = tmp_path / test_data["config_dir"]
    cfg_dir.mkdir()
    cfg_dirlock_fn = cfg_dir_src / Config.dirlock_fn
    shutil.copy(cfg_dirlock_fn, cfg_dir)
    cfg_fn = cfg_dir_src / Config.config_fn
    shutil.copy(cfg_fn, cfg_dir)
    active_fn = cfg_dir_src / SelectVocabulary.active_voca_info_fn
    shutil.copy(active_fn, cfg_dir)
    return cfg_dir


@pytest.fixture()
def config_object(
    config_dir_path: Path, mocker: MockerFixture, data_dir_path: Path
) -> Config:
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
    cfg = Config()
    return cfg


@pytest.fixture()
def database_object(
    setup_database_dir: Callable[[], Path],
    config_object: Config,
    test_data: PytestDataDict,
) -> Database:
    setup_database_dir()
    cfg = config_object
    voca_name = test_data["vocaname"]
    db = Database(cfg, voca_name)
    return db


@pytest.fixture()
def setup_database_dir(
    test_file_path: Path,
    test_data: PytestDataDict,
    data_dir_path: Path,
) -> Callable[[], Path]:
    def setup_() -> Path:
        data_dir = data_dir_path
        voca_name = test_data["vocaname"]
        dbname = Database.database_fn
        db_dir = Database.database_dir
        db_src_path = (
            test_file_path / test_data["data_dir"] / db_dir / voca_name / dbname
        )
        db_dest_path = data_dir / db_dir / voca_name
        db_dest_path.mkdir(parents=True)
        shutil.copy(db_src_path, db_dest_path)
        return db_dest_path

    return setup_


@pytest.fixture()
def main_window(
    config_object: Config,
    database_object: Database,
    qtbot: QtBot,
) -> MainWindow:
    db = database_object
    config = config_object
    # NOTE: QApplication.instance() returns a QCoreApplication type object,
    #     but there is no difference between QCoreApplication and QApplication
    #     see: https://stackoverflow.com/a/36561084/2173773
    app = typing.cast(QApplication, QApplication.instance())
    window = MainWindow(app, db, config)
    qtbot.add_widget(window)
    window.show()
    return window


@pytest.fixture()
def test_window(
    main_window: MainWindow,
    qtbot: QtBot,
) -> _TestWindow:
    window = main_window
    with qtbot.waitCallback() as callback:
        testwin = window.run_test()

        def gen_wrapper() -> Callable[[], None]:
            original_method = testwin.main_dialog
            _self = testwin

            def wrapper(*args: Any, **kwargs: Any) -> None:
                original_method(*args, **kwargs)
                callback(_self, *args, **kwargs)

            return wrapper

        wrapper = gen_wrapper()
        # TODO: see comment for test_main_dialog() above
        testwin.main_dialog = wrapper  # type: ignore
        idx = testwin.params.button_names.index("&Ok")
        testwin.params.buttons[idx].click()
    return testwin
