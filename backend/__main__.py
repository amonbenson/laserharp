from . import create_backend
from laserharp.app import LaserHarpApp
from laserharp.config import load_config

if __name__ == "__main__":
    laserharp = LaserHarpApp(load_config())
    backend = create_backend(laserharp)

    laserharp.start()
    backend.run(port=5000)
    laserharp.stop()
