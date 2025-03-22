from .physical import PhysicalCamera
from .emulated import EmulatedCamera
from ..env import getenv


EMULATOR = getenv("LH_EMULATOR", type=bool)


if EMULATOR:
    Camera = EmulatedCamera
else:
    Camera = PhysicalCamera
