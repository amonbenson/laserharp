import os
import sys
import logging
import argparse
from multiprocessing.connection import Listener
from .hex import hexdumps

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger("emulator")

if __name__ == "__main__":
    parser = argparse.ArgumentParser("laserharp emulator")
    parser.add_argument("--port", type=int, default=7500)
    parser.add_argument("--authkey", type=str, default="hwemu!23")
    args = parser.parse_args()

    listener = Listener(("localhost", args.port), authkey=args.authkey.encode("utf-8"))

    logger.info(f"Listening on port {args.port}. Use CTRL+C to exit.")

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
                    conn.send(msg)
                except EOFError:
                    break

            # close the connection
            conn.close()
            logger.info("Connection closed by the client.")

        except KeyboardInterrupt:
            logger.info("CTRL+C received. Exiting...")
            break

    # stop the listener and exit
    listener.close()
