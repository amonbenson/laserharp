import mido
from abc import ABC, abstractmethod
from enum import Enum


class MidiInterface(ABC):
    @abstractmethod
    def send(message: mido.Message):
        raise NotImplementedError()

    @abstractmethod
    def available() -> bool:
        raise NotImplementedError()

    @abstractmethod
    def read() -> mido.Message:
        raise NotImplementedError()


class DinMidiInterface(MidiInterface):
    def send(message: mido.Message):
        print("TODO: Din Midi Send")

    def available() -> bool:
        return False

    def read() -> mido.Message:
        return None


class MidiController():
    class Interface(Enum):
        DIN = 0
        USB = 1
        BLE = 2

    def __init__(self):
        self._interfaces = {
            MidiController.Interface.DIN: DinMidiInterface(),
            MidiController.Interface.USB: None,
            MidiController.Interface.BLE: None
        }

    def write(self, interface: Interface, message: mido.Message):
        self._interfaces[interface].send(message)

    def available(self, interface: Interface) -> bool:
        return self._interfaces[interface].available()
