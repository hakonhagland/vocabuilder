import shutil
from pathlib import Path, PosixPath

import pytest
from pytest_mock.plugin import MockerFixture

from vocabuilder.vocabuilder import Config, Database


@pytest.fixture(scope="session")
def test_file_path() -> PosixPath:
    return Path(__file__).parent / "files"


@pytest.fixture(scope="session")
def test_data() -> dict:
    return {
        "config_dir": "config",
        "data_dir": "data",
        "vocaname": "english-korean",
    }


@pytest.fixture(scope="session")
def config_dir_path(test_file_path: PosixPath, test_data: dict):
    cfg_dir = test_file_path / test_data["config_dir"]
    return cfg_dir


@pytest.fixture()
def data_dir_path(
    tmp_path: PosixPath, test_file_path: PosixPath, test_data: dict
) -> PosixPath:
    data_dir = tmp_path / test_data["data_dir"]
    data_dir.mkdir()
    data_dirlock_fn = (
        test_file_path / test_data["data_dir"] / Config.dirlock_fn
    )
    shutil.copy(data_dirlock_fn, data_dir)
    return data_dir


@pytest.fixture()
def config_object(
    config_dir_path: PosixPath, mocker: MockerFixture, data_dir_path: PosixPath
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
    tmp_path: PosixPath,
    test_file_path: PosixPath,
    config_object: Config,
    mocker: MockerFixture,
    test_data: dict,
    data_dir_path: PosixPath,
) -> Database:
    cfg = config_object
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
    db = Database(cfg, voca_name)
    return db