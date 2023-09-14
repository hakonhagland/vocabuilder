import configparser
import logging
import platformdirs
from pathlib import Path

from configparser import ConfigParser
import importlib.resources  # access non-code resources
from vocabuilder.exceptions import ConfigException


class Config:
    # NOTE: This is made a class variable since it must be accessible from
    #   pytest before creating an object of this class
    dirlock_fn = ".dirlock"
    config_fn = "config.ini"

    def __init__(self) -> None:
        self.appname = "vocabuilder"
        self.lockfile_string = "author=HH"
        self.config_dir = self.check_config_dir()
        self.config_path = Path(self.config_dir) / self.config_fn
        self.read_config()
        self.datadir_path = self.get_data_dir_path()

    def check_config_dir(self) -> Path:
        config_dir = platformdirs.user_config_dir(appname=self.appname)
        path = Path(config_dir)
        lock_file = path / self.dirlock_fn
        if path.exists():
            if path.is_file():
                raise ConfigException(
                    f"Config directory {str(path)} is file. Expected directory"
                )
            self.check_correct_config_dir(lock_file)
        else:
            path.mkdir(parents=True)
            with open(str(lock_file), "a", encoding="utf_8") as fp:
                fp.write(self.lockfile_string)
        return path

    def check_correct_config_dir(self, lock_file: Path) -> None:
        """The config dir might be owned by another app with the same name"""
        if lock_file.exists():
            if lock_file.is_file():
                with open(str(lock_file), encoding="utf_8") as fp:
                    line = fp.readline()
                    if line.startswith(self.lockfile_string):
                        return
                msg = "bad content"
            else:
                msg = "is a directory"
        else:
            msg = "missing"
        raise ConfigException(
            f"Unexpected: Config dir lock file: {msg}. "
            f"The data directory {str(lock_file.parent)} might be owned by another app."
        )

    def check_correct_data_dir(self, lock_file: Path) -> None:
        """The data dir might be owned by another app with the same name"""
        if lock_file.exists():
            if lock_file.is_file():
                with open(str(lock_file), encoding="utf_8") as fp:
                    line = fp.readline()
                    if line.startswith(self.lockfile_string):
                        return
                msg = "bad content"
            else:
                msg = "is a directory"
        else:
            msg = "missing"
        raise ConfigException(
            f"Unexpected: Data dir lock file: {msg}. "
            f"The data directory {str(lock_file.parent)} might be owned by another app."
        )

    def get_config_dir(self) -> Path:
        return self.config_dir

    def get_data_dir(self) -> Path:
        return self.datadir_path

    def get_data_dir_path(self) -> Path:
        data_dir = platformdirs.user_data_dir(appname=self.appname)
        path = Path(data_dir)
        lock_file = path / self.dirlock_fn
        if path.exists():
            if path.is_file():
                raise ConfigException(
                    f"Data directory {str(path)} is file. Expected directory"
                )
            self.check_correct_data_dir(lock_file)
        else:
            path.mkdir(parents=True)
            with open(str(lock_file), "a", encoding="utf_8") as fp:
                fp.write(self.lockfile_string)
        return path

    def get_config_path(self) -> Path:
        return self.config_path

    def get_section(self, section: str) -> configparser.SectionProxy:
        return self.config[section]

    def read_config(self) -> None:
        path = self.get_config_path()
        if path.exists():
            if not path.is_file():
                raise ConfigException(
                    f"Config filename {str(path)} exists, but filetype is not file"
                )
        else:
            with open(str(self.get_config_path()), "w", encoding="utf_8") as _:
                pass  # only create empty file
        config = configparser.ConfigParser()
        self.read_defaults(config)
        config.read(str(path))
        logging.info(f"Read config file: {str(path)}")
        self.config = config

    def read_defaults(self, config: ConfigParser) -> None:
        path = importlib.resources.files("vocabuilder.data").joinpath(
            "default_config.ini"
        )
        config.read(str(path))
