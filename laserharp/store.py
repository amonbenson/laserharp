import os
import logging
from typing import Optional
import sqlite3
import appdirs


DB_SCHEMA = """
CREATE TABLE `setting` (
    `id` INTEGER SERIAL PRIMARY KEY,
    `key` VARCHAR(255) NOT NULL UNIQUE,
    `value` TEXT NOT NULL
)
"""


class Store:
    DEFAULT_DB_FILE: str = os.path.abspath(os.path.join(appdirs.user_data_dir("laserharp"), "store.db"))

    def __init__(self, db_file: Optional[str] = None):
        self._db_file = db_file or self.DEFAULT_DB_FILE

        # connect to the database
        logging.info(f"Connecting to database at {self._db_file}")
        db_empty = not os.path.exists(self._db_file)
        self._db_conn = sqlite3.connect(self._db_file)

        # initialize the database
        if db_empty:
            logging.debug("Initializing new database")
            self._db_conn.execute(DB_SCHEMA)
            self._db_conn.commit()

    def fetch_settings(self) -> dict[str, str]:
        """
        Fetch all settings.
        """

        logging.debug("Fetching all settings.")
        res = self._db_conn.execute("SELECT `key`, `value` FROM `setting`")

        return {row[0]: row[1] for row in res.fetchall()}

    def fetch_setting(self, key: str) -> Optional[str]:
        """
        Fetch a single setting by key.
        """

        logging.debug(f"Fetching setting '{key}'")
        res = self._db_conn.execute("SELECT `value` FROM `setting` WHERE `key` = ?", (key,))

        row = res.fetchone()
        if not row:
            return None

        return row[0]

    def update_settings(self, settings: dict[str, str]):
        """
        Write multiple settings at once.
        """

        logging.debug("Updating multiple settings")
        with self._db_conn:
            self._db_conn.executemany("INSERT OR REPLACE INTO `setting` (`key`, `value`) VALUES (?, ?)", settings.items())

    def update_setting(self, key: str, value: str):
        """
        Write a single setting.
        """

        logging.debug(f"Updating setting '{key}' to '{value}'")
        with self._db_conn:
            self._db_conn.execute("INSERT OR REPLACE INTO `setting` (`key`, `value`) VALUES (?, ?)", (key, value))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    store = Store()

    print(store.fetch_settings())

    # store.update_setting("test", "a value")
    # print(store.fetch_setting("test"))

    # print(store.fetch_settings())
