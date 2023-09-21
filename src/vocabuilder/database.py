import logging
import typing

from vocabuilder.config import Config
from vocabuilder.firebase_database import FirebaseDatabase
from vocabuilder.local_database import LocalDatabase
from vocabuilder.mixins import TimeMixin
from vocabuilder.type_aliases import DatabaseRow


class Database(TimeMixin):
    def __init__(self, config: Config, voca_name: str) -> None:
        self.local_database = LocalDatabase(config, voca_name)
        self.firebase_database = FirebaseDatabase(config, voca_name)
        if self.firebase_database.is_initialized():
            self.push_updated_items_to_firebase()
        self.config = config
        self.voca_name = voca_name

    # public methods sorted alphabetically
    # ------------------------------------

    def add_item(self, item: DatabaseRow) -> None:
        self.local_database.add_item(item)

    def check_term1_exists(self, term1: str) -> bool:
        return self.local_database.check_term1_exists(term1)

    def create_backup(self) -> None:
        self.local_database.create_backup()

    def delete_item(self, term1: str) -> None:
        self.local_database.delete_item(term1)

    def push_updated_items_to_firebase(self) -> None:
        csv_items = self.local_database.get_items()
        logging.info(f"csv_items: {csv_items}")
        firebase_items = self.firebase_database.get_items()
        header = self.local_database.header
        num_items = 0
        logging.info("updating firebase..")
        for key, value in csv_items.items():
            if key in firebase_items:
                last_mod_local = int(typing.cast(str, value[header.last_modified]))
                last_mod_fb = int(
                    typing.cast(str, firebase_items[key][header.last_modified])
                )
                if last_mod_local > last_mod_fb:
                    logging.info(
                        f"Updating firebase item: {key} (local value is newer)"
                    )
                    self.firebase_database.push_item(key, value)
                    num_items += 1
            else:
                self.firebase_database.push_item(key, value)
                num_items += 1
        if num_items > 0:
            logging.info(f"Pushed {num_items} items to firebase")
        else:
            logging.info("No items pushed to firebase")

    def get_local_database(self) -> LocalDatabase:
        return self.local_database

    def get_pairs_exceeding_test_delay(self) -> list[tuple[str, str]]:
        return self.local_database.get_pairs_exceeding_test_delay()

    def get_random_pair(self) -> tuple[str, str] | None:
        return self.local_database.get_random_pair()

    def get_term1_data(self, term1: str) -> DatabaseRow:
        return self.local_database.get_term1_data(term1)

    def get_term1_list(self) -> list[str]:
        return self.local_database.get_term1_list()

    def get_term2(self, term1: str) -> str:
        return self.local_database.get_term2(term1)

    def get_voca_name(self) -> str:
        return self.local_database.get_voca_name()

    def update_item(self, term1: str, item: DatabaseRow) -> None:
        self.local_database.update_item(term1, item)

    def update_retest_value(self, term1: str, delay: int) -> None:
        self.local_database.update_retest_value(term1, delay)
