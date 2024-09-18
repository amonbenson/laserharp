import logging
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
import numpy as np
from perci import ReactiveNode, ReactiveDictNode


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
        self._min_value = int(desc.get("min", np.iinfo(np.int32).min))
        self._max_value = int(desc.get("max", np.iinfo(np.int32).max))
        self._default_value = int(desc.get("default", 0))

        # set the initial value
        self.set_value(self._default_value)

    def validate(self, value: Any) -> bool:
        try:
            value = int(value)
            return self._min_value <= value <= self._max_value
        except ValueError:
            logging.warning(f"Failed to parse value '{value}' as int")
            return False


class FloatSetting(Setting[float]):
    def __init__(self, key: str, target: ReactiveNode, desc: dict[str, Any]):
        super().__init__(key, target, desc)

        # parse the description
        self._min_value = float(desc.get("min", np.finfo(np.float32).min))
        self._max_value = float(desc.get("max", np.finfo(np.float32).max))
        self._default_value = float(desc.get("default", 0.0))

        # set the initial value
        self.set_value(self._default_value)

    def validate(self, value: Any) -> bool:
        try:
            value = int(value)
            return self._min_value <= value <= self._max_value
        except ValueError:
            logging.warning(f"Failed to parse value '{value}' as int")
            return False


class SettingsManager:
    SETTING_CLASSES = {
        "int": IntSetting,
        "float": FloatSetting,
    }

    def __init__(self, global_state: ReactiveDictNode):
        self._global_state = global_state
        self._settings = {}

    def setup(self):
        for component in self._global_state.keys():
            descriptions = self._global_state[component]["config"].setdefault("settings", {})
            targets = self._global_state[component].setdefault("settings", {})

            for key in descriptions.keys():
                # get the description node
                desc = descriptions.get_child(key)

                # create a new target node
                targets[key] = None
                target = targets.get_child(key)

                if "type" not in desc:
                    raise ValueError(f"Setting description for '{key}' in '{component}' does not have a type")

                setting_type = desc["type"]
                if setting_type not in self.SETTING_CLASSES:
                    raise ValueError(f"Setting type '{setting_type}' for '{key}' in '{component}' is not supported")

                # create the setting
                setting_class = self.SETTING_CLASSES[setting_type]

                logging.info(f"Creating setting '{component}.{key}' of type '{setting_type}'")
                self._settings[component + "." + key] = setting_class(key, target, desc)

    def get(self, component: str, key: str) -> Setting:
        return self._settings[component + "." + key]

    def set(self, component: str, key: str, value: Any):
        self.get(component, key).set_value(value)
