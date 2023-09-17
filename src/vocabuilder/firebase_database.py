import firebase_admin  # type: ignore
import firebase_admin.db  # type: ignore
import logging

from firebase_admin.exceptions import FirebaseError  # type: ignore
from vocabuilder.config import Config
from vocabuilder.csv_helpers import CsvDatabaseHeader

# from vocabuilder.local_database import LocalDatabase
from vocabuilder.mixins import TimeMixin


class FirebaseDatabase(TimeMixin):
    appname = "vocabuilder"

    def __init__(self, config: Config, voca_name: str):
        self.config = config
        self.voca_name = voca_name
        self.header = CsvDatabaseHeader()
        self.status = FirebaseStatus.NOT_INITIALIZED
        if self._read_config_parameters():
            if self._initialize_service_account():
                if self._get_database_reference():
                    if self.read_database():
                        self.status = FirebaseStatus.INITIALIZED
        logging.info(f"Firebase status: {self._status_string()}")

    # public methods sorted alphabetically
    # ------------------------------------

    def read_database(self) -> bool:
        try:
            snapshot = self.db.get()
        # FirebaseError is defined here:
        #   https://github.com/firebase/firebase-admin-python/
        #   blob/59a22b3ef3263530b1f1b61a3416ef311c24477b/firebase_admin/exceptions.py#L84
        except FirebaseError as exc:
            logging.info(
                "Firebase: could not get database content: cause:"
                f" {exc.cause}, error: {exc.code}, "
                f"http_response: {exc.http_response}"
            )
            return False
        if snapshot is None:
            logging.info("Firebase database is empty")
            return True
        self.data = {}
        for raw_key in snapshot.keys():
            item = snapshot[raw_key].copy()
            logging.info(f"Firebase: read item: {raw_key}, value: {item}")
            key = item.pop(self.header.term1)
            self.data[key] = item
        return True

    # private methods sorted alphabetically
    # -------------------------------------

    def _get_database_reference(self) -> bool:
        # https://firebase.google.com/static/docs/reference/admin/python/firebase_admin.db#reference_1
        try:
            self.db_root = firebase_admin.db.reference()
        except ValueError:
            logging.info("Firebase database reference is invalid")
            return False
        path = f"{self.appname}/{self.voca_name}"
        try:
            self.db = self.db_root.child(path)
        except ValueError:
            logging.info(f"firebase: invalid child path '{path}'")
            return False
        return True

    def _initialize_service_account(self) -> bool:
        # See: https://firebase.google.com/docs/admin/setup#python for more information
        try:
            # https://firebase.google.com/docs/reference/admin/python/firebase_admin.credentials#certificate
            cred = firebase_admin.credentials.Certificate(self.credentials_fn)
        except FileNotFoundError:
            logging.info("Firebase credentials file not found")
            return False
        except ValueError:
            logging.info("Firebase credentials file is invalid")
            return False
        # https://firebase.google.com/docs/reference/admin/python/firebase_admin#initialize_app
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
