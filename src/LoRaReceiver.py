import os
from dotenv import load_dotenv
from . import amqp_controller
import RPi.GPIO as GPIO
from time import sleep
from . import lcd_i2c
import json
import asyncio
# Load environment variables from .env file
load_dotenv()

# Access environment variables
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
display = lcd_i2c.lcd()


async def receive(lora):
    amqp_connection = amqp_controller.AMQPConnection(rabbitmq_server)
    await connect_to_rabbitmq(amqp_connection)
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
                    temp = f'T: {str(message_json["temperature"])}C'
                    hum = f'H: {str(message_json["humidity"])}%'
                    display.lcd_display_string(
                        get_formatted_datetime(message_json["timestamp"]), 1)
                    display.lcd_display_string(temp, 2)
                    display.lcd_display_string(hum, 2, 8)
                    print("with RSSI: {}\n".format(lora.packetRssi()))
                    # Invoke the method to send the message as AMQP
                    await amqp_connection.send_amqp_message(message)

                except Exception as e:
                    print(e)
    except KeyboardInterrupt:
        display.lcd_clear()
        print("Keyboard interrupt detected.")
    finally:
        await amqp_connection.close()


async def connect_to_rabbitmq(amqp_connection):
    while True:
        try:
            await amqp_connection.connect()
            print("Connection to RabbitMQ established successfully.")
            break
        except Exception as e:
            print(f"{e}. Retrying in 5 seconds...")
            await asyncio.sleep(5)


def get_formatted_datetime(dt):
    datetime_tuple = dt
    formatted_datetime = "{:04d}-{:02d}-{:02d} {:02d}:{:02d}".format(
        datetime_tuple[0], datetime_tuple[1], datetime_tuple[2],
        datetime_tuple[4], datetime_tuple[5])
    return formatted_datetime
