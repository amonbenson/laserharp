from abc import ABC, abstractmethod
from perci import ReactiveNode


class Component:
    def __init__(self, name: str, global_state: ReactiveNode):
        # check if the required configuration is present
        if name not in global_state["config"]:
            raise ValueError(f"Component {name} has no configuration")

        if name not in global_state["settings"]:
            raise ValueError(f"Component {name} has no settings")

        if name not in global_state["state"]:
            raise ValueError(f"Component {name} has no state")

        # store the name and configuration
        self.name = name
        self.config = global_state["config"][name]
        self.settings = global_state["settings"][name]
        self.state = global_state["state"][name]

    @property
    def enabled(self) -> bool:
        return self.config.get("enabled", True)

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
