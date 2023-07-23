import os
from dotenv import load_dotenv
import aio_pika
from . import ascon
# Load environment variables from .env file
load_dotenv()

# Access environment variables
rabbitmq_server = os.getenv('RABBITMQ_SERVER')

asc = ascon.Ascon()
# class RabbitMQConnectionError(Exception):
#     pass


class AMQPConnection:
    def __init__(self, host):
        self.host = host
        self.connection = None
        self.channel = None

    async def connect(self):
        try:
            self.connection = await aio_pika.connect_robust(self.host, heartbeat=30)
            self.channel = await self.connection.channel()
            await self.channel.declare_queue('ecg:esp32', durable=False)
        except Exception as e:
            raise Exception(f"Error connecting to RabbitMQ: {e}")

    async def close(self):
        await self.channel.close()
        await self.connection.close()

    async def send_amqp_message(self, message):
        try:
            await self.channel.default_exchange.publish(
                aio_pika.Message(
                    body=message,
                    delivery_mode=aio_pika.DeliveryMode.NOT_PERSISTENT
                ),
                routing_key='ecg:esp32'
            )
            print(f"*** Message send ***\n{asc.bytes_to_hex(message)}\n")
        except Exception as e:
            raise Exception(f"Error sending message: {e}")
