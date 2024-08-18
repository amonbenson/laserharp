from . import create_backend
from laserharp.app import LaserHarpApp
from laserharp.config import load_config

if __name__ == "__main__":
    laserharp = LaserHarpApp(load_config())
    backend, run = create_backend(laserharp)

    laserharp.start()
    run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    laserharp.stop()
