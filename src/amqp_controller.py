import os
from dotenv import load_dotenv
import aio_pika
import asyncio

# Load environment variables from .env file
load_dotenv()

# Access environment variables
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
print(rabbitmq_server)  # Output: my_value


async def send_amqp_message(server, message):
    # Establish connection
    connection = await aio_pika.connect_robust(server)

    # Create a channel
    channel = await connection.channel()

    # Declare the queue
    queue = await channel.declare_queue('my_queue', durable=True)

    # Publish the message to the queue
    await channel.default_exchange.publish(
        aio_pika.Message(
            body=message.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        ),
        routing_key='my_queue'
    )

    # Close the connection
    await connection.close()


async def receive():
    print("LoRa Receiver")
    while True:
        # if lora.receivedPacket():
        try:
            # payload = lora.read_payload()
            # message = payload.decode()
            print("*** Received message ***\n{}".format('hai'))
            # Invoke the callback function to send the message as AMQP
            await send_amqp_message(rabbitmq_server, 'hai')
        except Exception as e:
            print(e)
        # print("with RSSI: {}\n".format(lora.packetRssi()))
        await asyncio.sleep(2)

loop = asyncio.get_event_loop()

try:
    loop.create_task(receive())
    loop.run_forever()
except KeyboardInterrupt:
    pass
finally:
    loop.close()
