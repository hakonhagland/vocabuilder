from pathlib import Path, PosixPath
from vocabuilder.vocabuilder import Config
#from .fixtures.common import config_object, config_dir_path

def test_config_object(config_object: Config, config_dir_path: PosixPath):
    cfg = config_object
    cfg_dir = config_dir_path
    assert cfg.config_dir == cfg_dir
