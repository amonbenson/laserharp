import logging
import socket
import trio
import paho.mqtt.client as mqtt
from .component_v2 import Component
from .env import getenv


MQTT_HOST = getenv("LH_MQTT_HOST", type=str, default="localhost")
MQTT_PORT = getenv("LH_MQTT_PORT", type=int, default=1883)


class MQTTClient(Component):
    def __init__(self, *args, **kwargs):
        # forward-declare members
        self._client: mqtt.Client = None
        self._sock: socket.socket = None

        self._event_connect: trio.Event = None
        self._event_large_write: trio.Event = None
        self._event_should_read: trio.Event = None

        self._msg_send_channel: trio.MemorySendChannel = None
        self._msg_receive_channel: trio.MemoryReceiveChannel = None

        super().__init__(*args, **kwargs)

    def setup(self):
        self._client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
        self._sock = self._client.socket()

        # internal events
        self._event_connect = trio.Event()
        self._event_large_write = trio.Event()
        self._event_should_read = trio.Event()
        self._event_should_read.set()

        # register mqtt callbacks
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        self._client.on_socket_open = self._on_socket_open
        self._client.on_socket_close = self._on_socket_close
        self._client.on_socket_register_write = self._on_socket_register_write
        self._client.on_socket_unregister_write = self._on_socket_unregister_write

        # subscribed message channel
        self._msg_send_channel, self._msg_receive_channel = trio.open_memory_channel(100)

        # register mqtt loop tasks
        self.add_child("read_loop", self._read_loop)
        self.add_child("write_loop", self._write_loop)
        self.add_child("misc_loop", self._misc_loop)

    async def start(self):
        self._logger.info(f"Connecting to {MQTT_HOST}:{MQTT_PORT}...")
        self._client.connect(MQTT_HOST, MQTT_PORT)

    async def stop(self):
        self._logger.info("Disconnecting...")
        self._client.disconnect()

    async def _misc_loop(self):
        while self._client.loop_misc() == mqtt.MQTT_ERR_SUCCESS:
            await trio.sleep(1)

    async def _read_loop(self):
        while True:
            await self._event_should_read.wait()
            if self._sock.fileno() > 0:
                await trio.lowlevel.wait_readable(self._sock)
            else:
                await trio.sleep(0.1)
            self._client.loop_read()

    async def _write_loop(self):
        while True:
            await self._event_large_write.wait()
            if self._sock.fileno() > 0:
                await trio.lowlevel.wait_writable(self._sock)
            else:
                await trio.sleep(0.1)
            self._client.loop_write()

    def _on_connect(self, client, userdata, connect_flags, reason_code, properties):
        self._logger.info(f"Connected to {self._client.host}{self._client.port}")
        self._event_connect.set()

    def _on_disconnect(self, client, userdata, disconnect_flags, reason_code, properties):
        self._logger.info("Disconnected")
        self._event_connect = trio.Event()

    def _on_message(self, client, userdata, msg):
        pass
        # try:
        #     self._msg_send_channel.send_nowait(msg)
        # except trio.WouldBlock:
        #     print("Buffer full. Discarding an old msg!")
        #     # Take the old msg off the channel, discard it, and put the new msg on
        #     old_msg = self._msg_receive_channel.receive_nowait()
        #     # TODO: Store this old msg?
        #     self._msg_send_channel.send_nowait(msg)
        #     # Stop reading until the messages are read off the mem channel
        #     self._event_should_read = trio.Event()

    def _on_socket_open(self, client, userdata, sock):
        self._logger.debug("Socket opened")
        self._sock = sock
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 2048)

    def _on_socket_close(self, client, userdata, sock):
        self._logger.debug("Socket closed")

    def _on_socket_register_write(self, client, userdata, sock):
        self._logger.debug("Registered large write")
        # large write request - start write loop
        self._event_large_write.set()

    def _on_socket_unregister_write(self, client, userdata, sock):
        self._logger.debug("Unregistered large write")
        # finished large write - stop write loop
        self._event_large_write = trio.Event()
