from .physical_camera import PhysicalCamera
from .emulated_camera import EmulatedCamera
from ...common.env import getenv


EMULATOR = getenv("LH_EMULATOR", type=bool)


if EMULATOR:
    Camera = EmulatedCamera
else:
    Camera = PhysicalCamera


_global_camera = Camera()


def get_camera():
    return _global_camera
