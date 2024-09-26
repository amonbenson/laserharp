import os
import logging
import yaml
import shutil
from .dirs import CONFIG_DIR


DEFAULT_CONFIG_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "default", "config.yaml"))
CONFIG_FILE = os.path.abspath(os.path.join(CONFIG_DIR, "config.yaml"))


def init_config(filename: str):
    if not os.path.exists(DEFAULT_CONFIG_FILE):
        raise FileNotFoundError(f"Default configuration file not found: {DEFAULT_CONFIG_FILE}")

    # remove the target file if it exists
    if os.path.exists(filename):
        logging.info(f"Removing existing configuration file: {filename}")
        os.remove(filename)

    # create the target directory if it does not exist
    filedir = os.path.dirname(filename)
    if not os.path.exists(filedir):
        logging.info(f"Creating configuration directory: {filedir}")
        os.makedirs(filedir)

    # copy the default configuration file to the target location
    logging.info(f"Initializing configuration: {filename}")
    shutil.copy(DEFAULT_CONFIG_FILE, filename)


def load_config(filename: str = None, config_logging: bool = True) -> dict:
    if filename is None:
        filename = CONFIG_FILE

    # if the local configuration file does not exist, initialize it
    if not os.path.exists(filename):
        init_config(filename)

    # load the configuration
    logging.info(f"Loading configuration: {filename}")
    with open(filename, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f)

    # configure logging
    if config_logging:
        logging.basicConfig(
            level=_config["app"]["log_level"],
            format="%(asctime)s %(levelname)s %(pathname)s: %(message)s",
        )

    return _config


if __name__ == "__main__":
    import json

    config = load_config()

    print("Confguration:")
    print(json.dumps(config, indent=2))
