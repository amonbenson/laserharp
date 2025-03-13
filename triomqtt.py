import paho.mqtt.client as mqtt
import trio
import json
from trio_paho_mqtt import AsyncClient


async def handle_messages(client):
    async for msg in client.messages():
        print(f"Received msg: {msg.topic} {json.loads(msg.payload)}")


async def main():
    async with trio.open_nursery() as nursery:
        sync_client = mqtt.Client()
        client = AsyncClient(sync_client, nursery)
        client.connect("127.0.0.1", 1883, 60)

        client.subscribe("/lh/test")
        client.publish("/lh/test", json.dumps({ "message": "Hello World!" }))

        nursery.start_soon(handle_messages, client)


trio.run(main)
