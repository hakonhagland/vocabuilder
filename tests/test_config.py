from pathlib import PosixPath

from vocabuilder.vocabuilder import Config

# from .conftest import config_object, config_dir_path


def test_config_object(config_object: Config, config_dir_path: PosixPath) -> None:
    cfg = config_object
    cfg_dir = config_dir_path
    assert cfg.config_dir == cfg_dir
