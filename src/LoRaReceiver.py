import os
from dotenv import load_dotenv
from . import amqp_controller
import RPi.GPIO as GPIO
from time import sleep
from . import lcd_i2c
import json
import asyncio
from . import ascon
import binascii

load_dotenv()

display = lcd_i2c.lcd()

asc = ascon.Ascon()


async def receive(lora):
    rabbitmq_server = os.getenv('RABBITMQ_SERVER')
    key = os.getenv("ENCRYPT_KEY")
    nonce = os.getenv("ENCYPT_NONCE")
    amqp_connection = amqp_controller.AMQPConnection(rabbitmq_server)
    await connect_to_rabbitmq(amqp_connection)
    try:
        print("LoRa Receiver")
        while True:
            if lora.receivedPacket():
                lora.blink_led()
                try:
                    payload = lora.read_payload()
                    plaintext, nonce = decryption(
                        asc, binascii.unhexlify(payload), key, nonce, "CBC")
                    message = plaintext.decode("utf-8")
                    message_json = json.loads(message)
                    print(message_json)
                    temp = f'T: {str(message_json["t"])}C'
                    hum = f'H: {str(message_json["h"])}%'
                    show_on_lcd(display, [temp, hum])
                    # display.lcd_display_string(
                    #     get_formatted_date(message_json["tsp"]), 1)
                    # display.lcd_display_string(
                    #     get_formatted_time(message_json["tsp"]), 1, 12)
                    # show_on_lcd(display, [temp, hum])
                    print("*** Received message ***\n{}".format(message))
                    print("with RSSI: {}\n".format(lora.packetRssi()))
                    await amqp_connection.send_amqp_message(payload)
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
            show_on_lcd(display, ["Err connect to", "RabbitMQ Broker"])
            await asyncio.sleep(5)


def show_info(display, mes):
    temp = f'T: {str(mes["t"])}C'
    hum = f'H: {str(mes["h"])}%'
    display.lcd_display_string(
        get_formatted_date(mes["tsp"]), 1)
    display.lcd_display_string(
        get_formatted_time(mes["tsp"]), 1, 12)
    show_on_lcd(display, [temp, hum])


def show_on_lcd(lcd, items, delay=0):
    for x, text in enumerate(items):
        lcd.lcd_display_string(text, x)
    sleep(delay)


def get_formatted_date(date_tuple):
    return f"{date_tuple[0]:04d}-{date_tuple[1]:02d}-{date_tuple[2]:02d}"


def get_formatted_time(time_tuple):
    return f"{time_tuple[4]:02d}:{time_tuple[5]:02d}"


def decryption(ascon, ciphertext, key, nonce, mode="ECB"):
    key_bytes = key.encode('utf-8')
    if not isinstance(nonce, bytes):
        nonce = nonce.encode('utf-8')
    print(f"key: {key_bytes} len: {len(key_bytes)}")
    print(f"nonce: {nonce} len: {len(nonce)}")
    plaintext = ascon.ascon_decrypt(
        key_bytes, nonce, associateddata="", ciphertext=ciphertext,  variant="Ascon-128")
    if mode == "CBC":
        new_nonce = ciphertext[:16]
    return plaintext, new_nonce
