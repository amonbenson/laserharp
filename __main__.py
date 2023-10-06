import time
from .app import LaserHarpApp


if __name__ == '__main__':
    app = LaserHarpApp()
    app.start()

    # wait for keyboard interrupt
    try:
        while app.running:
            time.sleep(0.1)
    except KeyboardInterrupt:
        print("Keyboard interrupt received, stopping...")

    app.stop()
