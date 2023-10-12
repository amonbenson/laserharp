from multiprocessing import Process
from queue import Queue

from .advertisement import Advertisement
from .service import Application, Service, Characteristic, Descriptor
from .packet import BleMidiPacket

GATT_CHRC_IFACE = 'org.bluez.GattCharacteristic1'

class BleMidiAdvertisement(Advertisement):
    def __init__(self, index):
        Advertisement.__init__(self, index, 'peripheral')
        self.include_tx_power = True
        self.local_name = "Laser Harp"
        self.service_uuids = [BleMidiService.UUID]

class BleMidiService(Service):
    UUID = "03B80E5A-EDE8-4B33-A751-6CE34EC4C700"

    def __init__(self, index):
        Service.__init__(self, index, self.UUID, True)
        self.add_characteristic(BleMidiIOCharacteristic(self))

class BleMidiIOCharacteristic(Characteristic):
    UUID = "7772E5DB-3868-4112-A1A9-F2669D106BF3"

    def __init__(self, service):
        Characteristic.__init__(
            self,
            self.UUID,
            ['write', 'read', 'notify'],
            service)
        self.notifying = False

        self.rx_queue = Queue()

    def ReadValue(self, options):
        # read returns an empty payload
        return []

    def WriteValue(self, value, options):
        # parse the packet
        packet = BleMidiPacket.from_bytes(value)
        print(f"BLE RX: {packet.bytes().hex(' ')}")

        # put the packet into the queue
        self.rx_queue.put(packet)

    def StartNotify(self):
        if self.notifying: return

        self.notifying = True

    def StopNotify(self):
        if not self.notifying: return

        self.notify = True

    def tx(self, packet: BleMidiPacket):
        # send via notification
        print(f"BLE TX: {packet.bytes().hex(' ')}")
        self.PropertiesChanged(GATT_CHRC_IFACE, { 'Value': str(packet.bytes()) }, [])

    def rx(self):
        # get a packet from the queue (blocks the calling thread)
        return self.rx_queue.get()

class BleMidi():
    def __init__(self):
        self.app = Application()
        self.app.add_service(BleMidiService(0))
        self.app.register()
        self.io_characteristic = self.app.services[0].characteristics[0]

        self.adv = BleMidiAdvertisement(0)
        self.adv.register()

        self.process = Process(target=self._run)

    def _run(self):
        # run the app in a separate process
        try:
            self.app.run()
        except KeyboardInterrupt:
            self.app.quit()

    def start(self):
        self.process.start()

    def stop(self):
        self.app.quit()

        self.process.terminate()
        self.process.join()

    def send(self, packet: BleMidiPacket):
        self.io_characteristic.tx(packet)

    def read(self) -> BleMidiPacket:
        return self.io_characteristic.rx()
