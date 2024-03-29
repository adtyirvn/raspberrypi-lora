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
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
amqp_connection = amqp_controller.AMQPConnection(rabbitmq_server)


async def receive(lora):

    key = os.getenv("ENCRYPT_KEY")
    nonce = os.getenv("ENCYPT_NONCE")

    await connect_to_rabbitmq(amqp_connection)
    # print("LoRa Receiver")
    display.lcd_clear()
    display.lcd_display_string("waiting lora", 1)
    print("waiting lora")
    try:
        while True:
            if lora.receivedPacket():
                lora.blink_led()
                try:
                    payload = lora.read_payload()
                    payload_decode = payload.decode('utf-8')
                    payload_ascii = payload_decode.encode('ascii')
                    plaintext, nonce = decryption(
                        asc, binascii.unhexlify(payload_ascii), key, nonce, "CBC")
                    message = plaintext.decode("utf-8")
                    message_json = json.loads(message)
                    show_info(display, message_json)
                    print("\n*** Received message ***\n{}".format(message))
                    print("with RSSI: {}\n".format(lora.packetRssi()))
                    await amqp_connection.send_amqp_message(payload)
                except Exception as e:
                    print(e)
    except KeyboardInterrupt:
        display.lcd_clear()
        print("Keyboard interrupt detected.")
        await amqp_connection.close()
        display.lcd_display_string("closing", 1)
        display.lcd_display_string("goodbye...", 2)
        sleep(5)
        display.lcd_clear()


async def connect_to_rabbitmq(amqp_connection):
    while True:
        try:
            print("connecting...")
            display.lcd_clear()
            display.lcd_display_string("connecting...", 1)
            await amqp_connection.connect()
            print("connected")
            display.lcd_clear()
            display.lcd_display_string("connected", 1)
            sleep(3)
            break
        except Exception as e:
            print(e)
            display.lcd_clear()
            display.lcd_display_string("error connecting", 1)
            sleep(1)


def show_info(message):
    th = f'D: {message["rd"]}C V: {message["v"]}%'
    time = f'{get_formatted_date(message["tsp"])}'
    show_on_lcd([time, th])


def show_on_lcd(lcd, items, delay=0):
    for x, text in enumerate(items):
        lcd.lcd_display_string(text, x)
    sleep(delay)


def get_formatted_date(date_tuple):
    return f"{date_tuple[0]:04d}-{date_tuple[1]:02d}-{date_tuple[2]:02d} {date_tuple[4]:02d}:{date_tuple[5]:02d}"


def decryption(ascon, ciphertext, key, nonce, mode="ECB"):
    key_bytes = key.encode('utf-8')
    if not isinstance(nonce, bytes):
        nonce = nonce.encode('utf-8')
    # print(f"key: {key_bytes} len: {len(key_bytes)}")
    # print(f"nonce: {nonce} len: {len(nonce)}")
    plaintext = ascon.ascon_decrypt(
        key_bytes, nonce, associateddata="", ciphertext=ciphertext,  variant="Ascon-128")
    if mode == "CBC":
        new_nonce = ciphertext[:16]
    return plaintext, new_nonce
