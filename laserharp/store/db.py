import os
import sqlite3
import logging
from .dirs import DATA_DIR


DEFAULT_SCHEMA_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "default", "laserharp.sql"))
DB_FILE = os.path.abspath(os.path.join(DATA_DIR, "laserharp.db"))


def init_db(filename: str):
    if not os.path.exists(DEFAULT_SCHEMA_FILE):
        raise FileNotFoundError(f"Default schema file not found: {DEFAULT_SCHEMA_FILE}")

    # remove the target file if it exists
    if os.path.exists(filename):
        logging.info(f"Removing existing database file: {filename}")
        os.remove(filename)

    # create the target directory if it does not exist
    filedir = os.path.dirname(filename)
    if not os.path.exists(filedir):
        logging.info(f"Creating database directory: {filedir}")
        os.makedirs(filedir)

    # create the database file
    conn = sqlite3.connect(filename)

    # load the default schema
    with open(DEFAULT_SCHEMA_FILE, "r", encoding="utf-8") as f:
        schema = f.read()

    logging.info(f"Initializing database: {filename}")
    conn.executescript(schema)

    # commit and close the connection
    conn.commit()
    conn.close()


def load_db(filename: str = None) -> sqlite3.Connection:
    if filename is None:
        filename = DB_FILE

    # if the local database file does not exist, initialize it
    if not os.path.exists(filename):
        init_db(filename)

    # connect to the database
    logging.info(f"Connecting to database: {filename}")
    conn = sqlite3.connect(filename)
    return conn


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    conn = load_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM calibration")
    print("Calibration:")
    print(cursor.fetchall())

    cursor.execute("SELECT * FROM settings")
    print("Settings:")
    print(cursor.fetchall())

    conn.close()
