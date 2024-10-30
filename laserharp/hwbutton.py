import logging
from perci import ReactiveDictNode
from .component import Component
from .events import EventEmitter


class HWButton(Component, EventEmitter):
    def __init__(self, name: str, global_state: ReactiveDictNode):
        Component.__init__(self, name, global_state)
        EventEmitter.__init__(self)

    def start(self):
        pass

    def stop(self):
        pass

    def handle_ipc(self, message: bytes):
        # filter for button messages
        if message[0] != 0x90:
            return

        sequence = message[1:].decode("utf-8").lower()

        # check if the requested sequence is registered
        setting = f"sequence_{sequence}"
        print(setting, self.settings)
        if setting not in self.settings:
            logging.warning(f"Received button message for unregistered sequence: {sequence}")
            return

        # get the action and check if it is valid
        action = self.settings[setting]
        if action not in self.config["available_actions"]:
            logging.warning(f"Invalid action for button message: {action}")
            return

        # execute the action
        if action != "none":
            logging.debug(f"Executing button action: {sequence} -> {action}")
            self.emit(action)
