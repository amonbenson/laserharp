import time
import trio
import logging
import numpy as np


logger = logging.getLogger("lh:camera")


class PhysicalCamera:
    def __init__(self):
        self._frame_send_channel, self._frame_receive_channel = trio.open_memory_channel(0)

    @staticmethod
    def _camera_thread(frame_send_channel: trio.MemorySendChannel):
        # TODO: camera setup
        logger.info("Opening camera")
        time.sleep(1)

        while True:
            try:
                trio.from_thread.check_cancelled()

                time.sleep(0.5)
                frame = np.zeros((480, 640))

                trio.from_thread.run(frame_send_channel.send, frame)
            except trio.Cancelled:
                break

        # TODO: camera teardown
        logger.info("Closing camera")
        time.sleep(1)

    async def run(self, nursery: trio.Nursery):
        nursery.start_soon(trio.to_thread.run_sync, self._camera_thread, self._frame_send_channel)

    def frame_receive_channel(self) -> trio.MemoryReceiveChannel:
        return self._frame_receive_channel.clone()
