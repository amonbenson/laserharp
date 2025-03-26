from abc import ABC, abstractmethod
from typing import Optional
from .base import TopicComponent


class ConfigurableComponent(TopicComponent, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = {}

    def add_config(self, schema: dict):
        self.config = self.add_endpoint("config", schema=schema)
