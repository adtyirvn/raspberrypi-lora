import os
from dotenv import load_dotenv
from . import amqp_controller
import RPi.GPIO as GPIO
from time import sleep
from . import lcd_i2c
import json
from . import ascon
import binascii
import time
from . import config

load_dotenv()

display = lcd_i2c.lcd()
asc = ascon.Ascon()
rabbitmq_server = os.getenv('RABBITMQ_SERVER')
amqp_connection = amqp_controller.AMQPConnection(rabbitmq_server)
master_node = 'raspi'
node_one = 'esp32'

key_g = config.ENCRYPT_KEY
nonce_g = config.ENCRYPT_NONCE


async def receive(lora):
    try:
        msg_count = 0
        # display.lcd_clear()
        await connect_to_rabbitmq(amqp_connection)
        delay_ms = 4000
        previous_time = int(round(time.time() * 1000))
        # secs = 0
        while True:
            try:
                current_time = int(round(time.time() * 1000))
                elapsed_time = current_time - previous_time
                if elapsed_time >= delay_ms:
                    mes_dict = {
                        "idp": msg_count,
                        "id": master_node,
                        "to": node_one
                    }
                    if msg_count == 0:
                        mes_dict["rst"] = "reset"
                    mes_json = json.dumps(mes_dict)
                    lora.println(mes_json)
                    print(f"send: {mes_json}\n")
                    msg_count += 1
                    previous_time = current_time
                await on_receive(lora)
            except Exception as e:
                print(f"Error: {e}")
    except KeyboardInterrupt:
        display.lcd_clear()
        print("Keyboard interrupt detected.")
        await amqp_connection.close()
        show_on_lcd(["Closing", "Goodbye..."], 5)
        display.lcd_clear()


def receive_callback(lora):
    global nonce_g
    lora.blink_led()
    payload = lora.read_payload()
    plaintext, nonce_g = decryption(
        asc, payload, key_g, nonce_g, "CBC")
    message_json = plaintext.decode("utf-8")
    message_dict = json.loads(message_json)
    show_info(message_dict)
    print(f"*** Received message ***\n{message_dict}")
    print("with RSSI: {lora.packetRssi()}\n")
    return message_dict, payload


async def on_receive(lora):
    if lora.receivedPacket():
        payload, ciphertext = receive_callback(lora)
        if not len(payload):
            return
        recipient = payload["to"]
        sender = payload["id"]
        if recipient != node_one and recipient != master_node:
            return
        if sender == node_one:
            await amqp_connection.send_amqp_message(ciphertext)


async def connect_to_rabbitmq(amqp_connection):
    while True:
        try:
            print("Connecting...")
            display.lcd_clear()
            show_on_lcd(["Connecting to", "RabbitMQ Broker"])
            await amqp_connection.connect()
            print("Connected to RabbitMQ Broker")
            sleep(1)
            display.lcd_clear()
            show_on_lcd(["Connected to", "RabbitMQ broker"], 1)
            display.lcd_clear()
            break
        except Exception as e:
            print(e)
            display.lcd_clear()
            show_on_lcd(["Error, wait 5s", "Connecting..."], 5)


def show_info(message_json):
    th = f'T: {message_json["t"]}C H: {message_json["h"]}%'
    time = f'{get_formatted_date(message_json["tsp"])}'
    show_on_lcd([time, th])


def show_on_lcd(items, delay=0):
    for x, text in enumerate(items):
        display.lcd_display_string(text, x+1)
    sleep(delay)


def get_formatted_date(date_tuple):
    return f"{date_tuple[0]:04d}{date_tuple[1]:02d}{date_tuple[2]:02d} {date_tuple[4]:02d}:{date_tuple[5]:02d}:{date_tuple[6]:02d}"


def decryption(ascon, ciphertext, key, nonce, mode="ECB"):
    plaintext = ascon.ascon_decrypt(
        key, nonce, associateddata=b"", ciphertext=ciphertext,  variant="Ascon-128")
    if mode == "CBC":
        new_nonce = ciphertext[:16]
    return plaintext, new_nonce
