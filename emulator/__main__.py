import trio
from .emulator import Emulator


async def main():
    emulator = Emulator()

    try:
        await emulator.run()
    except* KeyboardInterrupt:
        pass


if __name__ == "__main__":
    trio.run(main)
