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

    async def _handle_config_change_task(self):
        while True:
            config = await self.config.wait_change()
            await self.handle_config_change(config)

    @abstractmethod
    async def handle_config_change(self, config: dict):
        pass
