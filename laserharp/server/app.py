from laserharp.config import load_config
from laserharp.app import LaserHarpApp
from . import create_backend

config = load_config()
laserharp = LaserHarpApp(config)
app, run = create_backend(laserharp)

# run the laserharp application
laserharp.start()
