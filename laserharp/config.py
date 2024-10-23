import os
import logging
import yaml


DEFAULT_CONFIG_FILENAME = os.path.abspath(os.path.join(os.path.dirname(__file__), "config.yaml"))


def load_config(filename: str = None, config_logging: bool = True, verbose_logging: bool = False):
    if filename is None:
        filename = DEFAULT_CONFIG_FILENAME

    if not os.path.exists(filename):
        raise FileNotFoundError(f"Config file not found at: {filename}")

    # load the configuration
    with open(filename, "r", encoding="utf-8") as f:
        _config = yaml.safe_load(f)

    # configure logging
    if config_logging:
        logging.basicConfig(
            level=_config["app"]["log_level"] if not verbose_logging else "DEBUG",
            format="%(asctime)s %(levelname)s %(pathname)s: %(message)s",
        )

    return _config


if __name__ == "__main__":
    import json

    config = load_config()

    print("Confguration:")
    print(json.dumps(config, indent=2))
