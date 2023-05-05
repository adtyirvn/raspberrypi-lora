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
        await self.channel.declare_queue('ecg:esp32', durable=True)

    async def close(self):
        await self.connection.close()

    async def send_amqp_message(self, message):
        await self.channel.default_exchange.publish(
            aio_pika.Message(
                body=message.encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key='ecg:esp32'
        )
