import os
import logging
import yaml


def load_config(filename: str = None, config_logging: bool = True):
    if filename is None:
        filename = os.path.abspath("./etc/config.yaml")

    # load the configuration
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
