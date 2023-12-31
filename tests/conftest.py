import logging
import shutil
import typing
from pathlib import Path
from typing import Any, Callable

import pytest
from PyQt6.QtWidgets import QApplication
from pytest_mock.plugin import MockerFixture

from vocabuilder.constants import TermStatus
from vocabuilder.csv_helpers import CsvDatabaseHeader
from vocabuilder.database import Database
from vocabuilder.local_database import LocalDatabase

# from vocabuilder.select_voca import SelectVocabulary
from vocabuilder.test_window import TestWindow as _TestWindow
from vocabuilder.vocabuilder import Config, MainWindow

from .common import GetConfig, GetDatabase, PytestDataDict, QtBot


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
    active_fn = cfg_dir_src / LocalDatabase.active_voca_info_fn
    shutil.copy(active_fn, cfg_dir)
    return cfg_dir


@pytest.fixture()
def get_config(
    config_dir_path: Path, mocker: MockerFixture, data_dir_path: Path
) -> GetConfig:
    def _config(setup_firebase: bool = False) -> Config:
        cfg_dir = config_dir_path
        data_dir = data_dir_path
        mocker.patch(
            "vocabuilder.config.platformdirs.user_config_dir",
            return_value=cfg_dir,
        )
        mocker.patch(
            "vocabuilder.config.platformdirs.user_data_dir",
            return_value=data_dir,
        )
        if setup_firebase:
            cfg_fn = cfg_dir / Config.config_fn
            cred_fn = credentials_file
            # NOTE: important the below string should start with a newline to avoid
            #       appending [Firebase] to the end of the last line in existing config
            #       file
            str_ = f"""
[Firebase]
credentials = {str(cred_fn)}
databaseURL = https://vocabuilder.firebasedatabase.app"""
            with open(str(cfg_fn), "a", encoding="utf_8") as fp:
                fp.write(str_)
        cfg = Config()
        return cfg

    return _config


@pytest.fixture()
def credentials_file(config_dir_path: Path) -> Path:
    cred_fn = config_dir_path / "credentials.json"
    cred_str = r"""{
  "type": "service_account",
  "project_id": "vocabuilder",
  "private_key_id": "xxxx",
  "private_key": "-----BEGIN PRIVATE KEY-----YomQoU1qLZ7S8=\n-----END PRIVATE KEY-----\n",
  "client_email": "firebase-adminsdk@vocabuilder.gserviceaccount.com",
  "client_id": "102",
  "auth_uri": "https://accounts.google.com/o/oauth2/auth",
  "token_uri": "https://oauth2.googleapis.com/token",
  "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
  "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/firebase-adminsdk-vocabuilder.gserviceaccount.com",
  "universe_domain": "googleapis.com"
}
"""  # noqa: B950
    with open(str(cred_fn), "w", encoding="utf_8") as fp:
        fp.write(cred_str)
    return cred_fn


@pytest.fixture()
def get_database(
    setup_database_dir: Callable[[], Path],
    config_dir_path: Path,
    get_config: GetConfig,
    test_data: PytestDataDict,
    mocker: MockerFixture,
) -> GetDatabase:
    def _database_object(init: bool = False) -> Database:
        setup_database_dir()
        voca_name = test_data["vocaname"]
        if init:
            cfg = get_config(setup_firebase=True)
            mocker.patch(
                "vocabuilder.firebase_database.firebase_admin.credentials.Certificate",
                return_value=None,
            )
            mocker.patch(
                "vocabuilder.firebase_database.firebase_admin.initialize_app",
                return_value=None,
            )
            mock = mocker.MagicMock()
            mocker.patch(
                "vocabuilder.firebase_database.firebase_admin.db.reference",
                return_value=mock,
            )
            child_mock = mocker.MagicMock()
            mock.child.return_value = child_mock
            logging.info(f"conftest: child_mock: {child_mock}")
            header = CsvDatabaseHeader()
            db_dict = {
                "NYJ18uc": {
                    header.term1: "apple",
                    header.term2: "사과",
                    header.test_delay: 1,
                    header.last_test: 1684886400,
                    header.last_modified: 1677329957,  # local db: 1687329957
                    header.status: TermStatus.NOT_DELETED,
                },
            }
            child_mock.get.return_value = db_dict
        else:
            cfg = get_config()
            mocker.patch(
                "vocabuilder.database.FirebaseDatabase._initialize_service_account",
                return_value=False,
            )
        db = Database(cfg, voca_name)
        return db

    return _database_object


@pytest.fixture()
def setup_database_dir(
    test_file_path: Path,
    test_data: PytestDataDict,
    data_dir_path: Path,
) -> Callable[[], Path]:
    def setup_() -> Path:
        data_dir = data_dir_path
        voca_name = test_data["vocaname"]
        dbname = LocalDatabase.database_fn
        db_dir = LocalDatabase.database_dir
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
    get_config: GetConfig,
    get_database: GetDatabase,
    qtbot: QtBot,
) -> MainWindow:
    db = get_database()
    config = get_config()
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
        window.run_test()
        testwin = typing.cast(_TestWindow, window.test_window)

        def gen_wrapper() -> Callable[[], None]:
            original_method = testwin.main_dialog
            _self = testwin

            def wrapper(*args: Any, **kwargs: Any) -> None:
                original_method(*args, **kwargs)
                callback(_self, *args, **kwargs)

            return wrapper

        wrapper = gen_wrapper()
        testwin.main_dialog = wrapper  # type: ignore
        idx = testwin.params.button_names.index("&Ok")
        testwin.params.buttons[idx].click()
    return testwin
