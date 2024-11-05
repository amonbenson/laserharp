import argparse
from laserharp.config import load_config
from laserharp.app import LaserHarpApp
from . import create_backend

if __name__ == "__main__":
    parser = argparse.ArgumentParser()

    parser.add_argument("-v", "--verbose", action="store_true", help="Enable verbose output")
    parser.add_argument("--ipc", action=argparse.BooleanOptionalAction, default=True, help="Enable the IPC interface. When disabled, no communication to the STM32 will be possible")
    parser.add_argument("--camera", action=argparse.BooleanOptionalAction, default=True, help="Enable the camera interface. When disabled, no interceptions can be detected and calibration will not be possible")
    parser.add_argument("--din-midi", action=argparse.BooleanOptionalAction, default=True, help="Enable the DIN MIDI interface. When disabled, no MIDI output will be generated")
    parser.add_argument("--send-standby", action=argparse.BooleanOptionalAction, default=True, help="Send a standby command to the STM32 board when stopping the application")

    args = parser.parse_args()

    config = load_config(verbose_logging=args.verbose)
    config["ipc"]["enabled"] = args.ipc
    config["camera"]["enabled"] = args.camera
    config["din_midi"]["enabled"] = args.din_midi
    config["app"]["send_standby"] = args.send_standby

    laserharp = LaserHarpApp(config)
    backend, run = create_backend(laserharp)

    laserharp.start()
    run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
    laserharp.stop()
