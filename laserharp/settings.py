import logging
import threading
import time
from abc import ABC, abstractmethod
from typing import Any, TypeVar, Generic, Optional, Union
from dataclasses import asdict
import numpy as np
from perci import ReactiveNode, ReactiveDictNode, create_queue_watcher
from .store import Store


T = TypeVar("T")
SettingRole = Union["client", "server"]


class Setting(ABC, Generic[T]):
    def __init__(self, key: str, target: ReactiveNode, desc: dict[str, Any]):
        self._key = key
        self._target = target
        self._desc = desc

        self._client_writable = desc.get("client_writable", True)

    def get_key(self) -> str:
        return self._key

    @abstractmethod
    def validate(self, value: Any) -> tuple[bool, Optional[T]]:
        pass

    def __str__(self) -> str:
        return str(self.get_value())

    def set_value(self, value: Any, *, role: SettingRole = "server"):
        # check permissions
        if role == "client" and not self._client_writable:
            raise ValueError(f"Setting '{self._key}' is not writable by the client")

        # parse and set the target value
        valid, parsed_value = self.validate(value)
        if valid:
            self._target.set_value(parsed_value)
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

    def validate(self, value: Any):
        try:
            value = int(value)
        except ValueError:
            return False, None

        if np.isnan(value):
            return False, None

        if value < self._min_value:
            return False, None

        if value > self._max_value:
            return False, None

        return True, value


class FloatSetting(Setting[float]):
    def __init__(self, key: str, target: ReactiveNode, desc: dict[str, Any]):
        super().__init__(key, target, desc)

        # parse the description
        self._min_value = desc["range"][0] if "range" in desc else np.finfo(np.float32).min
        self._max_value = desc["range"][1] if "range" in desc else np.finfo(np.float32).max
        self._default_value = float(desc.get("default", 0.0))

        # set the initial value
        self.set_value(self._default_value)

    def validate(self, value: Any):
        try:
            value = float(value)
        except ValueError:
            return False, None

        if np.isnan(value):
            return False, None

        if value < self._min_value:
            return False, None

        if value > self._max_value:
            return False, None

        return True, value


class StrSetting(Setting[str]):
    def __init__(self, key: str, target: ReactiveNode, desc: dict[str, Any]):
        super().__init__(key, target, desc)

        # parse the description
        self._default_value = str(desc.get("default", ""))

        # set the initial value
        self.set_value(self._default_value)

    def validate(self, value: Any):
        if not isinstance(value, str):
            return False, None

        return True, value


class BoolSetting(Setting[bool]):
    def __init__(self, key: str, target: ReactiveNode, desc: dict[str, Any]):
        super().__init__(key, target, desc)

        # parse the description
        self._default_value = bool(desc.get("default", False))

        # set the initial value
        self.set_value(self._default_value)

    def validate(self, value: Any):
        if isinstance(value, bool):
            return True, value
        if isinstance(value, str):
            return True, value.lower() in ["true", "1", "yes"]
        if isinstance(value, int):
            return True, value != 0
        else:
            return False, None

    def __str__(self) -> str:
        return "true" if self.get_value() else "false"


class SettingsManager:
    SETTING_CLASSES = {
        "int": IntSetting,
        "float": FloatSetting,
        "str": StrSetting,
        "bool": BoolSetting,
    }

    def __init__(self, global_state: ReactiveDictNode):
        self._global_state = global_state
        self._settings = {}

        self._store = Store()

        self._running = False
        self._thread = threading.Thread(target=self._run_store_thread)

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
                logging.debug(f"Creating setting '{component}.{key}' of type '{setting_type}'")
                setting_class = self.SETTING_CLASSES[setting_type]
                self._settings[component + "." + key] = setting_class(key, target, desc)

                # fetch the initial value from the store
                self._fetch_store(component, key)

        # add a watcher to the global state
        self._watcher = create_queue_watcher(self._global_state)

    def start(self):
        self._running = True
        self._thread.start()

    def stop(self):
        self._global_state.get_namespace().remove_watcher(self._watcher)
        self._running = False

    def _run_store_thread(self):
        while self._running:
            changes = self._watcher.get_changes()
            changed_settings = {}

            # gather all changed settings
            for change in changes:
                if change.change_type != "update":
                    continue

                # path should match root.<component>.settings.<key>
                if len(change.path) != 4:
                    continue

                if change.path[0] != "root" or change.path[2] != "settings":
                    continue

                component = change.path[1]
                key = change.path[3]
                changed_settings[component + "." + key] = change.value

            # store all changed settings
            for setting_key, value in changed_settings.items():
                self._store.update_setting(setting_key, str(value))

            time.sleep(1)

    def _fetch_store(self, component: str, key: str):
        value = self._store.fetch_setting(component + "." + key)
        if value is None:
            return

        try:
            logging.debug(f"Setting initial value '{value}' for setting '{component}.{key}'")
            self.get(component, key).set_value(value)
        except ValueError:
            logging.error(f"Failed to set initial value '{value}' for setting '{component}.{key}'")

    def has(self, component: str, key: str) -> bool:
        return component + "." + key in self._settings

    def get(self, component: str, key: str) -> Setting:
        if not self.has(component, key):
            raise ValueError(f"Setting '{component}.{key}' does not exist")
        return self._settings[component + "." + key]

    def set(self, component: str, key: str, value: Any, *, role: SettingRole = "server"):
        self.get(component, key).set_value(value, role=role)

        # update the store value
        # TODO: use a perci QueueWatcher to update the store in the background
        # self._store.update_setting(component + "." + key, str(value))
