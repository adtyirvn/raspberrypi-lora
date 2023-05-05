import os
from dotenv import load_dotenv
import aio_pika
import asyncio

# Load environment variables from .env file
load_dotenv()

# Access environment variables
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
print(rabbitmq_server)  # Output: my_value


class AMQPConnection:
    def __init__(self, host):
        self.host = host
        self.connection = None
        self.channel = None

    async def connect(self):
        self.connection = await aio_pika.connect_robust(self.host)
        self.channel = await self.connection.channel()
        await self.channel.declare_queue('my_queue', durable=True)

    async def close(self):
        await self.connection.close()

    async def send_amqp_message(self, message):
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key='my_queue'
        )

# Usage example


async def main():
    amqp_connection = AMQPConnection(rabbitmq_server)
    await amqp_connection.connect()

    try:
        lora = ...  # Initialize your LoRa object
        print("LoRa Receiver")
        while True:
            # if lora.receivedPacket():
            try:
                # payload = lora.read_payload()
                message = 'hai'
                print("*** Received message ***\n{}".format(message))
                # Invoke the method to send the message as AMQP
                await amqp_connection.send_amqp_message(message)
            except Exception as e:
                print(e)
            print("with RSSI: {}\n".format(lora.packetRssi()))
            await asyncio.sleep(0.1)  # Allow other tasks to run
    finally:
        await amqp_connection.close()

asyncio.run(main())
