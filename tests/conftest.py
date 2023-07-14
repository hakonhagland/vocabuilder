import shutil
from pathlib import Path

import pytest
from pytest_mock.plugin import MockerFixture
from typing import Callable

from vocabuilder.vocabuilder import Config, Database
from .common import PytestDataDict


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


@pytest.fixture(scope="session")
def config_dir_path(test_file_path: Path, test_data: PytestDataDict) -> Path:
    cfg_dir = test_file_path / test_data["config_dir"]
    return cfg_dir


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
