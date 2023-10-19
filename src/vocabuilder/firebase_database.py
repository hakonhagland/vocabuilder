import firebase_admin  # type: ignore
import firebase_admin.db  # type: ignore
import logging

from firebase_admin.exceptions import FirebaseError  # type: ignore
from vocabuilder.config import Config
from vocabuilder.csv_helpers import CsvDatabaseHeader

# from vocabuilder.local_database import LocalDatabase
from vocabuilder.mixins import TimeMixin
from vocabuilder.type_aliases import DatabaseRow, DatabaseType


class FirebaseStatus:
    NOT_INITIALIZED = 0
    INITIALIZED = 1


class FirebaseDatabase(TimeMixin):
    appname = "vocabuilder"

    def __init__(self, config: Config, voca_name: str):
        self.config = config
        self.voca_name = voca_name
        self.header = CsvDatabaseHeader()
        self.status = FirebaseStatus.NOT_INITIALIZED
        self.data: DatabaseType = {}
        if self._read_config_parameters():
            if self._initialize_service_account():
                if self._get_database_reference():
                    if self.read_database():
                        self.status = FirebaseStatus.INITIALIZED
        logging.info(f"Firebase status: {self._status_string()}")

    # public methods sorted alphabetically
    # ------------------------------------

    def get_items(self) -> DatabaseType:
        return self.data

    def is_initialized(self) -> bool:
        return self.status == FirebaseStatus.INITIALIZED

    def push_item(self, key: str, value: DatabaseRow) -> None:
        object = value.copy()
        object[self.header.term1] = key
        try:
            self.db.push(object)
        except FirebaseError as exc:
            logging.info(
                "Firebase: could not push item: cause:"
                f" {exc.cause}, error: {exc.code}, "
                f"http_response: {exc.http_response}"
            )
            return
        except ValueError:
            logging.info(f"Firebase: invalid value error: {object}")
            return
        except TypeError:
            logging.info(f"Firebase: invalid type error: {object}")
            return
        logging.info(f"Firebase: pushed item: '{key}'")

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
        self.data = {}
        if snapshot is None:
            logging.info("Firebase database is empty")
            return True
        num_duplicates = 0
        num_items = 0
        logging.info("Firebase: reading database..")
        for raw_key in snapshot.keys():
            item = snapshot[raw_key].copy()
            # logging.info(f"Firebase: read item: {raw_key}, value: {item}")
            key = item.pop(self.header.term1)
            if key in self.data:
                num_duplicates += 1
                lm1 = self.data[key][self.header.last_modified]
                lm2 = item[self.header.last_modified]
                if lm1 > lm2:  # old value is newer, so do nothing
                    continue
            self.data[key] = item
            num_items += 1
        if num_duplicates > 0:
            logging.info(f"Firebase: found {num_duplicates} duplicate items")
        logging.info(f"Firebase: read {num_items} items from database")
        return True

    def run_reset(self) -> None:
        logging.info("Firebase: running cleanup..")
        # self.db.delete()

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
