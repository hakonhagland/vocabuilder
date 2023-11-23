# import logging
import re
from pathlib import Path
from typing import Any, Callable

import pytest
from pytest_mock.plugin import MockerFixture

from vocabuilder.exceptions import ConfigException
from vocabuilder.vocabuilder import Config

# from .common import QtBot, P


class TestContructor:
    def test_config_object(self, config_object: Config, config_dir_path: Path) -> None:
        cfg = config_object
        cfg_dir = config_dir_path
        assert cfg.config_dir == cfg_dir

    @pytest.mark.parametrize("path_exists", [True, False])
    def test_cfg_dir(
        self, path_exists: bool, mocker: MockerFixture, data_dir_path: Path
    ) -> None:
        data_dir = data_dir_path
        mocker.patch(
            "vocabuilder.config.platformdirs.user_config_dir",
            return_value=data_dir,
        )
        mocker.patch(
            "vocabuilder.config.platformdirs.user_data_dir",
            return_value=data_dir,
        )

        def gen_wrapper() -> Callable[[Any, Any], None]:
            original_method = Config.read_config
            if path_exists:

                def wrapper(self: Config, **kwargs: Any) -> None:
                    self.config_path = Path(self.config_dir) / "foobar"
                    self.config_path.mkdir(parents=True)
                    original_method(self, **kwargs)

            else:

                def wrapper(self: Config, **kwargs: Any) -> None:
                    self.config_path = Path(self.config_dir) / "foobar.ini"
                    original_method(self, **kwargs)

            return wrapper  # type: ignore

        wrapper = gen_wrapper()
        mocker.patch("vocabuilder.vocabuilder.Config.read_config", wrapper)
        if path_exists:
            with pytest.raises(ConfigException) as excinfo:
                Config()
            assert re.search(r"filetype is not file", str(excinfo))
        else:
            Config()
            assert True

    @pytest.mark.parametrize("path_is_file", [False, True])
    def test_data_dir(
        self,
        path_is_file: bool,
        config_dir_path: Path,
        mocker: MockerFixture,
        data_dir_path: Path,
    ) -> None:
        data_dir = data_dir_path / "foobar"
        if path_is_file:
            with open(str(data_dir), "w", encoding="utf_8") as fp:
                fp.write("xyz")
        cfg_dir = config_dir_path
        mocker.patch(
            "vocabuilder.config.platformdirs.user_config_dir",
            return_value=cfg_dir,
        )
        mocker.patch(
            "vocabuilder.config.platformdirs.user_data_dir",
            return_value=data_dir,
        )
        if path_is_file:
            with pytest.raises(ConfigException) as excinfo:
                Config()
            assert re.search(r"Expected directory", str(excinfo))
        else:
            Config()
            assert True


class TestOther:
    def test_get_dir(self, config_object: Config, config_dir_path: Path) -> None:
        cfg = config_object
        cfg_dir = config_dir_path
        assert cfg.get_config_dir() == cfg_dir

    @pytest.mark.parametrize(
        "is_dir, bad_content", [(False, False), (True, False), (False, True)]
    )
    def test_data_dir_lock_file(
        self, is_dir: bool, bad_content: bool, config_object: Config
    ) -> None:
        cfg = config_object
        data_dir = cfg.get_data_dir()
        lock_file = data_dir / "xyz"
        if is_dir:
            lock_file.mkdir(parents=True)
        if bad_content:
            with open(str(lock_file), "w", encoding="utf_8") as fp:
                fp.write("xyz")
        with pytest.raises(ConfigException) as excinfo:
            cfg.check_correct_data_dir(lock_file)
        if not is_dir and not bad_content:
            assert re.search(r"Data dir lock file: missing", str(excinfo))
        elif is_dir and not bad_content:
            assert re.search(r"Data dir lock file: is a directory", str(excinfo))
        elif not is_dir and bad_content:
            assert re.search(r"Data dir lock file: bad content", str(excinfo))

    @pytest.mark.parametrize(
        "is_dir, bad_content", [(False, False), (True, False), (False, True)]
    )
    def test_config_dir_lock_file(
        self, is_dir: bool, bad_content: bool, config_object: Config
    ) -> None:
        cfg = config_object
        data_dir = cfg.get_data_dir()
        lock_file = data_dir / "xyz"
        if is_dir:
            lock_file.mkdir(parents=True)
        if bad_content:
            with open(str(lock_file), "w", encoding="utf_8") as fp:
                fp.write("xyz")
        with pytest.raises(ConfigException) as excinfo:
            cfg.check_correct_config_dir(lock_file)
        if not is_dir and not bad_content:
            assert re.search(r"Config dir lock file: missing", str(excinfo))
        elif is_dir and not bad_content:
            assert re.search(r"Config dir lock file: is a directory", str(excinfo))
        elif not is_dir and bad_content:
            assert re.search(r"Config dir lock file: bad content", str(excinfo))

    @pytest.mark.parametrize("path_is_file", [False, True])
    def test_config_dir(
        self,
        path_is_file: bool,
        config_object: Config,
        mocker: MockerFixture,
        data_dir_path: Path,
    ) -> None:
        cfg = config_object
        cfg_dir_fake = data_dir_path / "foobar"
        mocker.patch(
            "vocabuilder.config.platformdirs.user_config_dir",
            return_value=cfg_dir_fake,
        )
        if path_is_file:
            with open(str(cfg_dir_fake), "w", encoding="utf_8") as fp:
                fp.write("xyz")
        if path_is_file:
            with pytest.raises(ConfigException) as excinfo:
                cfg.check_config_dir()
            assert re.search(r"Expected directory", str(excinfo))
        else:
            path = cfg.check_config_dir()
            assert path == cfg_dir_fake
