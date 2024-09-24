from abc import ABC, abstractmethod
from perci import ReactiveDictNode


class Component:
    def __init__(self, name: str, global_state: ReactiveDictNode):
        if name not in global_state:
            raise ValueError(f"Component {name} not found in global state")
        component_state = global_state[name]

        # make sure the required configuration is present
        if "config" not in component_state:
            raise ValueError(f"Component {name} has no configuration")

        if "settings" not in component_state:
            component_state["settings"] = {}

        if "state" not in component_state:
            component_state["state"] = {}

        # setup the name and configuration
        self.name = name
        self.config = global_state[name]["config"]
        self.settings = global_state[name]["settings"]
        self.state = global_state[name]["state"]

    @property
    def enabled(self) -> bool:
        return self.config.get("enabled", True)

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
