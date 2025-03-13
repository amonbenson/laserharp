import trio
from ..common.mqtt import get_mqtt_client

async def main():
    mqtt = get_mqtt_client()

if __name__ == "__main__":
    trio.run(main)
