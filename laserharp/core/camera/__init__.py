import os
from .physical_camera import PhysicalCamera
from .emulated_camera import EmulatedCamera


EMULATOR = bool(os.getenv("LH_EMULATOR"))


if EMULATOR:
    Camera = EmulatedCamera
else:
    Camera = PhysicalCamera


_global_camera = Camera()
def get_camera():
    return _global_camera
