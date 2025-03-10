import os
import sys
import logging
from multiprocessing.connection import Listener
from .hex import hexdumps

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

logger = logging.getLogger("emulator")

if __name__ == "__main__":
    port = int(os.getenv("LH_EMULATOR_SERIAL_PORT", 7500))
    authkey = os.getenv("LH_EMULATOR_SERIAL_AUTHKEY", "lhemu!23").encode("utf-8")
    listener = Listener(("localhost", port), authkey=authkey)

    logger.info(f"Listening on port {port}. Use CTRL+C to exit.")

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
