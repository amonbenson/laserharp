from abc import ABC, abstractmethod
from typing import Optional
from .base import TopicComponent


class ConfigurableComponent(TopicComponent, ABC):
    DEFAULT_CONFIG_SCHEMA = {
        "type": "object",
    }

    def add_config(self, default: Optional[dict] = None, schema: Optional[dict] = None):
        if default is None:
            default = {}
        if schema is None:
            schema = self.DEFAULT_CONFIG_SCHEMA

        self.config = self.add_endpoint("config", default=default, schema=schema)
