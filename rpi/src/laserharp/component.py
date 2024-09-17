from abc import ABC, abstractmethod
from perci import ReactiveNode


class Component:
    def __init__(self, name: str, config: ReactiveNode, settings: ReactiveNode):
        self._name = name
        self._config = config
        self._settings = settings
        self._state = None

        self._enabled = config.get("enabled", True)

    def get_name(self) -> str:
        return self._name

    def get_config(self) -> ReactiveNode:
        return self._config

    def get_state(self) -> ReactiveNode:
        if self._state is None:
            raise ValueError("Component state is not initialized")

        return self._state

    def is_enabled(self) -> bool:
        return self._enabled

    @abstractmethod
    def start(self):
        pass

    @abstractmethod
    def stop(self):
        pass
