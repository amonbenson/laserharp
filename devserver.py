from backend import create_backend
from laserharp.app import LaserHarpApp
from laserharp.config import load_config
import subprocess

if __name__ == "__main__":
    laserharp = LaserHarpApp(load_config())
    backend = create_backend(laserharp)
    frontend = subprocess.Popen(["yarn", "dev"], cwd="frontend")

    laserharp.start()

    # run the backend. This will block until a keyboard interrupt is received
    backend.run(port=5000, debug=True)

    # stop the frontend process and laserharp app
    frontend.kill()
    laserharp.stop()
