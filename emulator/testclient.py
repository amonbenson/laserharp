import os
import sys
import select
import traceback
import time
from multiprocessing.connection import Client, Connection
from threading import Thread, Lock
from .hex import hexparse, hexdumps

def recv_thread(conn: Connection):
    while not conn.closed:
        try:
            # wait for a message
            while not conn.poll(0.1):
                pass
            if conn.closed:
                return

            # receive and print message
            msg = conn.recv()
            print(f"emulator >>> (RX) {hexdumps(msg)}")
        except EOFError:
            print("\nConnection closed by the server. Exiting...")
            conn.close()
            break

if __name__ == "__main__":
    port = int(os.getenv("LH_EMULATOR_SERIAL_PORT", 7500))
    authkey = os.getenv("LH_EMULATOR_SERIAL_AUTHKEY", "lhemu!23").encode("utf-8")

    conn = Client(("localhost", port), authkey=authkey)
    print(f"Connected to {port}. Write your message in hex format (e. g. \"12 34 ab ef\"). Use CTRL+D to exit.")

    try:
        # setup receiver and sender threads
        recv_t = Thread(target=recv_thread, args=(conn,), daemon=True)
        recv_t.start()

        # wait until the connection got closed or the exit event is set
        while not conn.closed:
            try:
                # # wait for input from stdin
                # while not select.select([sys.stdin], [], [], 0.1)[0]:
                #     pass

                # # read a line from stdin
                # line = sys.stdin.readline().strip()
                line = input("emulator <<< (TX) ")

                # convert to bytes
                try:
                    msg = hexparse(line)
                except Exception as e:
                    print(f"Failed to parse: {e}")
                    continue

                # if len(msg) != 4:
                #     print(f"Failed to parse: invalid length ({len(msg)}). Should be 4")
                #     continue

                # send the message
                conn.send(msg)

                time.sleep(0.01) # wait a bit in case the server responds immediately
            except KeyboardInterrupt:
                print()
            except EOFError:
                print("\nEOF received from console. Exiting...")
                conn.close()
                break

        # close the connection and join the receiver thread
        if not conn.closed:
            conn.close()
        recv_t.join()

    except Exception:
        traceback.print_exc()
    finally:
        conn.close()
        print("Connection closed.")
