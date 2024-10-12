from serial import Serial
from ..config import load_config

def test_serial(name: str, port: str, baudrate: int, test_byte: int):
    serial = Serial(port, baudrate)

    print(f"Sending byte to {name} at {port}")
    serial.write(test_byte.to_bytes(1, "big"))

    serial.timeout = 1
    res = serial.read(1)
    if not res:
        print(f"Did not receive a response. Make sure {port} is configured to loop back to itself.")
    elif res != test_byte.to_bytes(1, "big"):
        print(f"Received unexpected response: {res}")
    else:
        print("Received expected response.")

    serial.close()

if __name__ == "__main__":
    config = load_config()

    # test both serial ports
    test_serial("Din Midi Serial", config["din_midi"]["port"], config["din_midi"]["baudrate"], 0x90)
    test_serial("IPC Serial", config["ipc"]["port"], config["ipc"]["baudrate"], 0x01)
