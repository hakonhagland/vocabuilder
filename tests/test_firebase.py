import logging

# import re
from firebase_admin.exceptions import FirebaseError  # type: ignore
from pathlib import Path

import pytest
from _pytest.logging import LogCaptureFixture
from pytest_mock.plugin import MockerFixture
from vocabuilder.firebase_database import FirebaseDatabase
from vocabuilder.vocabuilder import Config
from .common import PytestDataDict

# from .conftest import database_object, test_data, data_dir_path


class TestAddItem:
    def append_to_config_file(self, cfg_fn: Path, str_: str) -> None:
        with open(str(cfg_fn), "a", encoding="utf_8") as fp:
            fp.write(str_)

    def create_credentials_file(self, config_dir_path: Path) -> Path:
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

    @pytest.mark.parametrize(
        "file_not_found, file_invalid, cred_missing, url_missing",
        [
            (True, False, False, False),
            (False, True, False, False),
            (False, False, True, False),
            (False, False, False, True),
        ],
    )
    def test_init_failure(
        self,
        file_not_found: bool,
        file_invalid: bool,
        cred_missing: bool,
        url_missing: bool,
        caplog: LogCaptureFixture,
        config_dir_path: Path,
        data_dir_path: Path,
        test_data: PytestDataDict,
        mocker: MockerFixture,
    ) -> None:
        caplog.set_level(logging.INFO)
        cfg_fn = config_dir_path / Config.config_fn
        cred_fn = self.create_credentials_file(config_dir_path)
        if cred_missing:
            str_ = """[Firebase]
"""
        elif url_missing:
            str_ = f"""[Firebase]
credentials = {str(cred_fn)}
"""
        else:
            str_ = f"""[Firebase]
credentials = {str(cred_fn)}
databaseURL = https://vocabuilder.firebasedatabase.app"""
        self.append_to_config_file(cfg_fn, str_)
        mocker.patch(
            "vocabuilder.config.platformdirs.user_config_dir",
            return_value=config_dir_path,
        )
        mocker.patch(
            "vocabuilder.config.platformdirs.user_data_dir",
            return_value=data_dir_path,
        )
        cfg = Config()
        voca_name = test_data["vocaname"]
        if file_not_found:
            mocker.patch(
                "vocabuilder.firebase_database.firebase_admin.credentials.Certificate",
                side_effect=FileNotFoundError,
            )
        elif file_invalid:
            mocker.patch(
                "vocabuilder.firebase_database.firebase_admin.credentials.Certificate",
                side_effect=ValueError,
            )
        else:
            mocker.patch(
                "vocabuilder.firebase_database.firebase_admin.credentials.Certificate",
                return_value=None,
            )
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.initialize_app",
            return_value=None,
        )
        FirebaseDatabase(cfg, voca_name)
        if file_not_found or file_invalid or cred_missing or url_missing:
            if file_not_found:
                assert caplog.records[-2].msg.startswith(
                    "Firebase credentials file not found"
                )
            elif file_invalid:
                assert caplog.records[-2].msg.startswith(
                    "Firebase credentials file is invalid"
                )
            elif cred_missing:
                assert caplog.records[-2].msg.startswith(
                    "Missing firebase credentials in config file"
                )
            elif url_missing:
                assert caplog.records[-2].msg.startswith(
                    "Missing firebase databaseURL in config file"
                )
            assert caplog.records[-1].msg.startswith("Firebase status: NOT_INITIALIZED")

    @pytest.mark.parametrize(
        "ref_error, child_error", [(True, False), (False, True), (False, False)]
    )
    def test_init(
        self,
        ref_error: bool,
        child_error: bool,
        caplog: LogCaptureFixture,
        config_dir_path: Path,
        data_dir_path: Path,
        test_data: PytestDataDict,
        mocker: MockerFixture,
    ) -> None:
        caplog.set_level(logging.INFO)
        cfg_fn = config_dir_path / Config.config_fn
        cred_fn = self.create_credentials_file(config_dir_path)
        str_ = f"""[Firebase]
credentials = {str(cred_fn)}
databaseURL = https://vocabuilder.firebasedatabase.app"""
        self.append_to_config_file(cfg_fn, str_)
        mocker.patch(
            "vocabuilder.config.platformdirs.user_config_dir",
            return_value=config_dir_path,
        )
        mocker.patch(
            "vocabuilder.config.platformdirs.user_data_dir",
            return_value=data_dir_path,
        )
        cfg = Config()
        voca_name = test_data["vocaname"]
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.credentials.Certificate",
            return_value=None,
        )
        mocker.patch(
            "vocabuilder.firebase_database.firebase_admin.initialize_app",
            return_value=None,
        )
        if ref_error:
            mocker.patch(
                "vocabuilder.firebase_database.firebase_admin.db.reference",
                side_effect=ValueError,
            )
        else:
            mock = mocker.MagicMock()
            mocker.patch(
                "vocabuilder.firebase_database.firebase_admin.db.reference",
                return_value=mock,
            )
            if child_error:
                mock.child.side_effect = ValueError
        FirebaseDatabase(cfg, voca_name)
        if ref_error:
            assert caplog.records[-2].msg.startswith(
                "Firebase database reference is invalid"
            )
        if child_error:
            assert caplog.records[-2].msg.startswith("firebase: invalid child path")
        if ref_error or child_error:
            assert caplog.records[-1].msg.startswith("Firebase status: NOT_INITIALIZED")
        else:
            assert caplog.records[-1].msg.startswith("Firebase status: INITIALIZED")

    @pytest.mark.parametrize(
        "get_error, db_empty", [(True, False), (False, True), (False, False)]
    )
    def test_read(
        self,
        get_error: bool,
        db_empty: bool,
        caplog: LogCaptureFixture,
        config_dir_path: Path,
        data_dir_path: Path,
        test_data: PytestDataDict,
        mocker: MockerFixture,
    ) -> None:
        caplog.set_level(logging.INFO)
        cfg_fn = config_dir_path / Config.config_fn
        cred_fn = self.create_credentials_file(config_dir_path)
        str_ = f"""[Firebase]
credentials = {str(cred_fn)}
databaseURL = https://vocabuilder.firebasedatabase.app"""
        self.append_to_config_file(cfg_fn, str_)
        mocker.patch(
            "vocabuilder.config.platformdirs.user_config_dir",
            return_value=config_dir_path,
        )
        mocker.patch(
            "vocabuilder.config.platformdirs.user_data_dir",
            return_value=data_dir_path,
        )
        cfg = Config()
        voca_name = test_data["vocaname"]
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
        if get_error:
            child_mock.get.side_effect = FirebaseError(
                "code", "message", cause=None, http_response=None
            )
        elif db_empty:
            child_mock.get.return_value = None
        else:
            db_dict = {"NYJ18uc": {"Term1": "100", "Status": "1"}}
            child_mock.get.return_value = db_dict
        FirebaseDatabase(cfg, voca_name)
        if get_error:
            assert caplog.records[-2].msg.startswith(
                "Firebase: could not get database content"
            )
        elif db_empty:
            assert caplog.records[-2].msg.startswith("Firebase database is empty")
        else:
            assert caplog.records[-2].msg.startswith(
                "Firebase: read item: NYJ18uc, value: {'Term1': '100', 'Status': '1'}"
            )
        if get_error:
            assert caplog.records[-1].msg.startswith("Firebase status: NOT_INITIALIZED")
        else:
            assert caplog.records[-1].msg.startswith("Firebase status: INITIALIZED")
