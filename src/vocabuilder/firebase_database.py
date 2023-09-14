import firebase_admin  # type: ignore
import logging

from vocabuilder.config import Config

# from vocabuilder.local_database import LocalDatabase
from vocabuilder.mixins import TimeMixin


class FirebaseDatabase(TimeMixin):
    def __init__(self, config: Config, voca_name: str):
        self.config = config
        self.voca_name = voca_name
        self.status = FirebaseStatus.NOT_INITIALIZED
        if self._read_config_parameters():
            if self._initialize_service_account():
                self.status = FirebaseStatus.INITIALIZED
        logging.info(f"Firebase status: {self._status_string()}")

    def _initialize_service_account(self) -> bool:
        # See: https://firebase.google.com/docs/admin/setup#python for more information
        try:
            cred = firebase_admin.credentials.Certificate(self.credentials_fn)
        except FileNotFoundError:
            logging.info("Firebase credentials file not found")
            return False
        except ValueError:
            logging.info("Firebase credentials file is invalid")
            return False
        firebase_admin.initialize_app(cred, options={"databaseURL": self.database_url})
        return True

    def _read_config_parameters(self) -> bool:
        try:
            cfg_firebase = self.config.get_section("Firebase")
        except KeyError:
            logging.info("Missing section [Firebase] in config file")
            return False
        try:
            self.credentials_fn = cfg_firebase["credentials"]
        except KeyError:
            logging.info("Missing firebase credentials in config file")
            return False
        try:
            self.database_url = cfg_firebase["databaseURL"]
        except KeyError:
            logging.info("Missing firebase databaseURL in config file")
            return False
        return True

    def _status_string(self) -> str:
        if self.status == FirebaseStatus.NOT_INITIALIZED:
            return "NOT_INITIALIZED"
        elif self.status == FirebaseStatus.INITIALIZED:
            return "INITIALIZED"
        else:
            return "UNKNOWN"  # pragma: no cover


class FirebaseStatus:
    NOT_INITIALIZED = 0
    INITIALIZED = 1
