import os
from dotenv import load_dotenv
import asyncio
from . import amqp_controller

# Load environment variables from .env file
load_dotenv()

# Access environment variables
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
print(rabbitmq_server)  # Output: my_value


async def receive(lora):
    amqp_connection = amqp_controller.AMQPConnection(rabbitmq_server)
    await amqp_connection.connect()

    try:
        print("LoRa Receiver")
        while True:
            if lora.receivedPacket():
                try:
                    payload = lora.read_payload()
                    message = payload.encode('utf-8')
                    print("*** Received message ***\n{}".format(message))
                    # Invoke the method to send the message as AMQP
                    await amqp_connection.send_amqp_message(message)
                except Exception as e:
                    print(e)
            # print("with RSSI: {}\n".format(lora.packetRssi()))
            await asyncio.sleep(0.1)  # Allow other tasks to run
    finally:
        await amqp_connection.close()
