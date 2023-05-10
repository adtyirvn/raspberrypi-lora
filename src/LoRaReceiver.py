import os
from dotenv import load_dotenv
from . import amqp_controller
import RPi.GPIO as GPIO
from time import sleep
from . import lcd_i2c
import json
# Load environment variables from .env file
load_dotenv()

# Access environment variables
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
display = lcd_i2c.lcd()


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
                    message_json = json.loads(message)
                    print("*** Received message ***\n{}".format(message))
                    print(message_json["temperature"])
                    display.lcd_display_string("Received message", 1)
                    display.lcd_display_string(message_json["temperature"], 2)
                    # Invoke the method to send the message as AMQP
                    await amqp_connection.send_amqp_message(message)

                except Exception as e:
                    print(e)
            # print("with RSSI: {}\n".format(lora.packetRssi()))
            # await asyncio.sleep(0.1)  # Allow other tasks to run
    finally:
        await amqp_connection.close()
