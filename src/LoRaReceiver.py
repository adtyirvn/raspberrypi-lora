import os
from dotenv import load_dotenv
from . import amqp_controller
import RPi.GPIO as GPIO
from time import sleep
import drivers
# Load environment variables from .env file
load_dotenv()

# Access environment variables
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
display = drivers.Lcd()


async def receive(lora):
    amqp_connection = amqp_controller.AMQPConnection(rabbitmq_server)
    await amqp_connection.connect()

    try:
        print("LoRa Receiver")
        while True:
            if lora.receivedPacket():
                lora.blink_led()
                try:
                    payload = lora.read_payload()
                    message = payload.decode('utf-8')
                    print("*** Received message ***\n{}".format(message))
                    display.lcd_display_string('Received message', 1)
                    # Invoke the method to send the message as AMQP
                    await amqp_connection.send_amqp_message(message)
                    display.lcd_clear()
                except Exception as e:
                    print(e)
            # print("with RSSI: {}\n".format(lora.packetRssi()))
            # await asyncio.sleep(0.1)  # Allow other tasks to run
    finally:
        await amqp_connection.close()
