import logging
import time
from .app import LaserHarpApp


if __name__ == '__main__':
    app = LaserHarpApp()
    app.start(force_calibration=False)

    # wait for keyboard interrupt
    try:
        while app.state != LaserHarpApp.State.IDLE:
            time.sleep(0.1)
    except KeyboardInterrupt:
        logging.info("Keyboard interrupt")

    app.stop()
