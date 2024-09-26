import os
import logging
from abc import ABC, abstractmethod
from typing import Any, Optional, TypeVar, Generic
import yaml
import numpy as np
from perci import ReactiveNode, ReactiveDictNode, reactive
from .db import load_db


DESCRIPTIONS_FILE = os.path.abspath(os.path.join(os.path.dirname(__file__), "default", "settings.yaml"))

T = TypeVar("T")


class Setting(ABC, Generic[T]):
    def __init__(self, key: str, target: ReactiveNode, desc: dict[str, Any]):
        self._key = key
        self._target = target
        self._desc = desc

    def get_key(self) -> str:
        return self._key

    @abstractmethod
    def validate(self, value: Any) -> bool:
        pass

    def set_value(self, value: Any):
        if self.validate(value):
            self._target.set_value(value)
        else:
            raise ValueError(f"Invalid value for setting {self._key}")

    def get_value(self) -> T:
        return self._target.get_value()


class IntSetting(Setting[int]):
    def __init__(self, key: str, target: ReactiveNode, desc: dict[str, Any]):
        super().__init__(key, target, desc)

        # parse the description
        self._min_value = desc["range"][0] if "range" in desc else np.iinfo(np.int32).min
        self._max_value = desc["range"][1] if "range" in desc else np.iinfo(np.int32).max
        self._default_value = int(desc.get("default", 0))

        # set the initial value
        self.set_value(self._default_value)

    def validate(self, value: Any) -> bool:
        if not isinstance(value, int):
            return False

        if value < self._min_value:
            return False

        if value > self._max_value:
            return False

        return True


class FloatSetting(Setting[float]):
    def __init__(self, key: str, target: ReactiveNode, desc: dict[str, Any]):
        super().__init__(key, target, desc)

        # parse the description
        self._min_value = desc["range"][0] if "range" in desc else np.finfo(np.float32).min
        self._max_value = desc["range"][1] if "range" in desc else np.finfo(np.float32).max
        self._default_value = float(desc.get("default", 0.0))

        # set the initial value
        self.set_value(self._default_value)

    def validate(self, value: Any) -> bool:
        if not isinstance(value, float):
            return False

        if value < self._min_value:
            return False

        if value > self._max_value:
            return False

        return True


class SettingsManager:
    SETTING_CLASSES = {
        "int": IntSetting,
        "float": FloatSetting,
    }

    def __init__(self, global_state: ReactiveDictNode, descriptions_file: Optional[str] = None):
        self._global_state = global_state
        self._settings = {}

        # load settings descriptions
        if descriptions_file is None:
            descriptions_file = DESCRIPTIONS_FILE
        with open(descriptions_file, "r", encoding="utf-8") as f:
            self._descriptions = yaml.safe_load(f)

        # connect to the database
        self._db = load_db()

    def setup(self):
        cursor = self._db.cursor()

        # add a global settings object
        if "settings" not in self._global_state:
            self._global_state["settings"] = {}

        for key, desc in self._descriptions.items():
            # create a new target node
            self._global_state["settings"][key] = None
            target = self._global_state["settings"].get_child(key)

            if "type" not in desc:
                raise ValueError(f"Setting description for '{key}' does not have a type")

            setting_type = desc["type"]
            if setting_type not in self.SETTING_CLASSES:
                raise ValueError(f"Setting type '{setting_type}' for '{key}' is not supported")

            # create the setting object
            setting_class = self.SETTING_CLASSES[setting_type]

            logging.info(f"Creating setting '{key}' of type '{setting_type}'")
            self._settings[key] = setting_class(key, target, desc)

            # fetch the current value from the database if it exists
            res = cursor.execute("SELECT `value` FROM settings WHERE `key` = ?", (key,))
            if row := res.fetchone():
                value = row[0]
                logging.debug(f"Reading value for setting '{key}': {value}")
                self._settings[key].set_value(value)

    def has(self, key: str) -> bool:
        return key in self._settings

    def __getitem__(self, key: str) -> Setting:
        if not self.has(key):
            raise ValueError(f"Setting '{key}' does not exist")
        return self._settings[key]

    def __setitem__(self, key: str, value: Any):
        # update the setting object
        self[key].set_value(value)

        # update the database
        logging.debug(f"Writing value for setting '{key}': {value}")
        cursor = self._db.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (`key`, `value`) VALUES (?, ?)", (key, value))


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)

    # write example description
    with open("/tmp/settings_test.yaml", "w", encoding="utf-8") as f:
        f.write(
            """    
test_0:
    type: int
    range: [0, 100]
    default: 50
"""
        )

    # create a global state
    global_state = reactive()

    # create a settings manager
    settings = SettingsManager(global_state, descriptions_file="/tmp/settings_test.yaml")
    settings.setup()

    settings["test_0"] = 100
