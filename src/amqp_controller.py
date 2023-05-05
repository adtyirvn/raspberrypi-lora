import os
from dotenv import load_dotenv
import aio_pika
import asyncio

# Load environment variables from .env file
load_dotenv()

# Access environment variables
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
print(rabbitmq_server)  # Output: my_value


async def send_amqp_message(message):
    # Establish connection
    connection = await aio_pika.connect_robust('amqp://guest:guest@localhost/')

    # Create a channel
    channel = await connection.channel()

    # Declare the queue
    queue = await channel.declare_queue('my_queue', durable=True)

    # Publish the message to the queue
    await queue.publish(
        aio_pika.Message(
            body=message.encode(),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT
        )
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
            await send_amqp_message('hai')
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
