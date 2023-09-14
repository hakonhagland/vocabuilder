import logging

# import re
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
            (False, False, False, False),
            (False, False, True, False),
            (False, False, False, True),
        ],
    )
    def test_add_ok(
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
        else:
            assert caplog.records[-1].msg.startswith("Firebase status: INITIALIZED")
