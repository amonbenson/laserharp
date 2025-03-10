import os
import sys
import logging
import argparse
from multiprocessing.connection import Listener
from .hex import hexdumps
from .webinterface import start_web_interface, stop_web_interface, send_event

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger("emulator")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("laserharp emulator")
    parser.add_argument("--port", type=int, default=7500)
    parser.add_argument("--authkey", type=str, default="hwemu!23")
    parser.add_argument("--web", action="store_true")
    parser.add_argument("--web-host", nargs="?", const="0.0.0.0", default="127.0.0.1")
    parser.add_argument("--web-port", type=int, default=5000)
    args = parser.parse_args()

    # start the web interface if enabled
    if args.web:
        start_web_interface(args.web_host, args.web_port)

    # start the listener
    listener = Listener(("localhost", args.port), authkey=args.authkey.encode("utf-8"))
    logger.info(f"Listening on port {args.port}. Use CTRL+C to exit.")

    # wait for messages
    while True:
        try:
            # wait for a new connection
            logger.info(f"Waiting for a connection...")
            conn = listener.accept()
            logger.info(f"Connected to {listener.last_accepted[0]}:{listener.last_accepted[1]}")

            # handle events until EOF is received
            while True:
                try:
                    msg = conn.recv()
                    logging.debug(f"Received message: {hexdumps(msg)}")
                    send_event(msg)
                except EOFError:
                    break

            # close the connection
            conn.close()
            logger.info("Connection closed by the client.")

        except KeyboardInterrupt:
            logger.info("CTRL+C received. Exiting...")
            break

    # stop the listener
    listener.close()

    # stop the web interface
    if args.web:
        stop_web_interface()
