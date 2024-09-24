import logging
import time
from .app import LaserHarpApp
from .config import load_config


if __name__ == "__main__":
    app = LaserHarpApp(load_config())
    app.start(force_calibration=False)

    # wait for keyboard interrupt
    try:
        while app.state != LaserHarpApp.State.IDLE:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt")

    app.stop()
