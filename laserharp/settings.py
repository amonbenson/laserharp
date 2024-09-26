import logging
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic
import numpy as np
from perci import ReactiveNode, ReactiveDictNode
from .store import Store


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

    def __init__(self, global_state: ReactiveDictNode):
        self._global_state = global_state
        self._settings = {}

        self._store = Store()

    def setup(self):
        for component in self._global_state.keys():
            if "settings" not in self._global_state[component]["config"]:
                self._global_state[component]["config"]["settings"] = {}
            descriptions = self._global_state[component]["config"]["settings"]

            if "settings" not in self._global_state[component]:
                self._global_state[component]["settings"] = {}
            targets = self._global_state[component]["settings"]

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

                # fetch the initial value from the store
                if value := self._store.fetch_setting(component + "." + key):
                    self._settings[component + "." + key].set_value(value)

    def has(self, component: str, key: str) -> bool:
        return component + "." + key in self._settings

    def get(self, component: str, key: str) -> Setting:
        if not self.has(component, key):
            raise ValueError(f"Setting '{component}.{key}' does not exist")
        return self._settings[component + "." + key]

    def set(self, component: str, key: str, value: Any):
        self.get(component, key).set_value(value)

        # update the store value
        # TODO: use a perci QueueWatcher to update the store in the background
        self._store.update_setting(component + "." + key, value)
