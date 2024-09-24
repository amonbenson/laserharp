import logging
import time
import serial
from perci import ReactiveDictNode
from .component import Component


class IPCController(Component):
    BYTE_TIMEOUT = 0.01

    def __init__(self, name: str, global_state: ReactiveDictNode, custom_serial=None):
        super().__init__(name, global_state)

        if not self.enabled:
            self._serial = None
        elif custom_serial is not None:
            self._serial = custom_serial
        else:
            self._serial = serial.Serial(
                port=self.config["port"],
                baudrate=self.config["baudrate"],
                parity=serial.PARITY_NONE,
                stopbits=serial.STOPBITS_ONE,
                bytesize=serial.EIGHTBITS,
            )

    def start(self):
        if not self.enabled:
            logging.info("IPC interface is disabled")
            return

        if not self._serial.is_open:
            self._serial.open()

    def stop(self):
        if not self.enabled:
            return

        self._serial.close()

    def send_raw(self, data: bytes, timeout=1.0):
        # only short messages are supported
        if len(data) != 4:
            raise ValueError(f"IPC Data must be 4 bytes long, got {len(data)}")

        # send the packet
        logging.debug(f"RPI -> STM: {data.hex(' ')}")

        if self.enabled:
            self._serial.write_timeout = timeout
            self._serial.write(data)
            # self._serial.flush()

    def read_raw(self, timeout=1.0) -> bytes:
        if not self.enabled:
            time.sleep(timeout)
            return None

        # read the cable number and code index
        self._serial.timeout = timeout
        try:
            data0 = self._serial.read(1)
        except KeyboardInterrupt:
            return None
        if len(data0) == 0:
            return None

        # read the remaining packet
        self._serial.timeout = self.BYTE_TIMEOUT * 3
        data1 = self._serial.read(3)
        if len(data1) != 3:
            raise ValueError("Read timeout")

        data = data0 + data1
        logging.debug(f"STM -> RPI: {data.hex(' ')}")
        return data
